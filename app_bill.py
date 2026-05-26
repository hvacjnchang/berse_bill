# app.py
import streamlit as st
import sqlite3
import pandas as pd
import streamlit.components.v1 as components

# 核心連動匯入
from database_init import init_database
from calculations import calculate_benchmarks, calculate_score_and_level, generate_detailed_process

# 網頁設定
st.set_page_config(page_title="BERSe 2024 計算與列印系統", layout="wide", page_icon="🏢")

# 嵌入列印優化 CSS (@media print)
st.markdown("""
<style>
    /* 一般分級標籤樣式 */
    .rating-box { padding: 15px; border-radius: 10px; color: white; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .level-1plus { background-color: #006400; border: 3px solid #FFD700; }
    .level-1 { background-color: #228B22; }
    .level-2 { background-color: #32CD32; }
    .level-3 { background-color: #ADFF2F; color: black; }
    .level-4 { background-color: #FFD700; color: black; }
    .level-5 { background-color: #FF8C00; }
    .level-6 { background-color: #FF4500; }
    .level-7 { background-color: #8B0000; }
    .report-table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }
    .report-table th, .report-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    .report-table th { background-color: #f2f2f2; }

    /* 🖨️ 瀏覽器列印專用 CSS 媒體查詢 */
    @media print {
        /* 隱藏所有 Streamlit 原生介面元素，如側邊欄、上方工具列、重整按鈕 */
        header, 
        [data-testid="stSidebar"], 
        footer,
        div[class^="stButton"],
        div.stDownloadButton,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        iframe,
        .no-print {
            display: none !important;
        }
        /* 確保列印主體展開至最大寬度，無邊距 */
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        /* 列印區域強制換頁或維持適當 A4 寬度 */
        .printable-area {
            display: block !important;
            width: 100% !important;
            color: #000 !important;
            background: #fff !important;
        }
        /* 避免表格或計算過程跨頁斷開 */
        .report-table, .printable-area div {
            page-break-inside: avoid;
        }
    }
</style>
""", unsafe_allow_html=True)

# 啟動時自動初始化資料庫
init_database()

# 資料庫查詢輔助函式
def query_db(query, params=()):
    conn = sqlite3.connect("berse_2024.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

st.title("🏢 BERSe 2024 建築能效計算(電費單版)")
st.caption("內建完整計算推導過程展示，支援一鍵轉存 PDF 與 A4 規範列印")
st.write("---")

# 側邊欄輸入設定
st.sidebar.header("📁 第一步：地點與類別")
case_name = st.sidebar.text_input("案件名稱", "台北科技總部大樓")
case_address = st.sidebar.text_input("建築地址", "台北市信義區信義路")
floor_area = st.sidebar.number_input("評估樓地板面積 Ae (㎡)", min_value=1.0, value=5000.0, step=100.0)

# 行政區聯動
counties = query_db("SELECT DISTINCT county FROM regional_ur")["county"].tolist()
selected_county = st.sidebar.selectbox("請選擇縣市", counties)

districts = query_db("SELECT district FROM regional_ur WHERE county = ?", (selected_county,))["district"].tolist()
selected_district = st.sidebar.selectbox("請選擇鄉鎮市區", districts)

ur_info = query_db("SELECT zone, ur_value FROM regional_ur WHERE county = ? AND district = ?", (selected_county, selected_district)).iloc[0]
ur_zone, ur_value = ur_info["zone"], ur_info["ur_value"]
st.sidebar.info(f"📍 城鄉係數定位：{ur_zone}區 (UR = {ur_value})")

# 建築類別聯動
categories = query_db("SELECT DISTINCT category FROM building_params")["category"].tolist()
selected_category = st.sidebar.selectbox("建築大分類", categories)

subcategories = query_db("SELECT subcategory FROM building_params WHERE category = ?", (selected_category,))["subcategory"].tolist()
selected_subcategory = st.sidebar.selectbox("副分類 (小分類)", subcategories)

building_params = query_db("SELECT aeui, leui, eteui, hpeui, eeui FROM building_params WHERE category = ? AND subcategory = ?", (selected_category, selected_subcategory)).iloc[0]
aeui, leui, eteui, hpeui, eeui = building_params["aeui"], building_params["leui"], building_params["eteui"], building_params["hpeui"], building_params["eeui"]

# 12個月用電數據輸入
st.sidebar.header("⚡ 第二步：年度用電")
total_raw_kwh = st.sidebar.number_input("12個月累積總用電量 (kWh)", min_value=0.0, value=420000.0, step=5000.0)
green_kwh = st.sidebar.number_input("再生能源自用度數 (kWh/yr)", min_value=0.0, value=20000.0, step=1000.0)

# 核心計量計算
adjusted_kwh = max(0.0, total_raw_kwh - green_kwh)
eui_raw = total_raw_kwh / floor_area
eui_adjusted = adjusted_kwh / floor_area

eui_n, eui_g, eui_max = calculate_benchmarks(ur_value, aeui, leui, eteui, hpeui, eeui)
score, level, css_class = calculate_score_and_level(eui_adjusted, eui_n, eui_g, eui_max)

# 生成計算過程 Markdown (不含 HTML 標籤，支援數學公式)
detailed_process_markdown = generate_detailed_process(
    ur_value, aeui, leui, eteui, hpeui, eeui, 
    total_raw_kwh, green_kwh, floor_area, 
    eui_adjusted, eui_n, eui_g, eui_max, score, level
)

# 分頁籤：區分工作控制台與正式列印區
tab1, tab2 = st.tabs(["🖥️ 能效試算工作台", "📄 計算書預覽與列印（含詳細過程）"])

with tab1:
    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.subheader("📊 基準指標對比")
        chart_data = pd.DataFrame({
            "指標項目": ["近零碳基準 (EUI_n)", "本案 EUI*", "綠建築基準 (EUI_g)", "限制值基準 (EUI_max)"],
            "EUI 值 (kWh/㎡·yr)": [eui_n, eui_adjusted, eui_g, eui_max]
        })
        st.bar_chart(chart_data.set_index("指標項目"))
        
    with col_r:
        st.subheader("🏆 試算結果")
        st.markdown(f'<div class="rating-box {css_class}">最終能效等級：{level}</div>', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("能效得分 (Score)", f"{score:.2f} 分")
        m2.metric("調整後 EUI*", f"{eui_adjusted:.2f}", f"原始: {eui_raw:.1f}")
        
    st.write("---")
    st.markdown(detailed_process_markdown)

with tab2:
    st.warning("💡 提示：本頁面排版已套用 A4 列印格式。您可以使用下方的「列印」按鈕直接轉存為 PDF，或利用鍵盤快捷鍵 `Ctrl+P` 進行列印。列印時側邊欄與功能按鈕會自動隱藏。")
    
    # 建立 JS 連動列印按鈕
    components.html("""
    <button onclick="window.parent.print()" style="
        background-color: #008CBA; 
        color: white; 
        padding: 12px 24px; 
        border: none; 
        border-radius: 5px; 
        cursor: pointer; 
        font-size: 16px;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">🖨️ 立即列印此計算書 / 儲存為 PDF (A4 格式)</button>
    """, height=65)

    # 用於預覽/列印的正式格式區 (將表格 HTML 與 Markdown 計算明細分開渲染，防止縮排造成 Markdown code block 錯誤)
    st.markdown('<div class="printable-area" style="background-color: white; padding: 20px; border: 1px dashed #ccc; border-radius: 5px; color: #333;">', unsafe_allow_html=True)
    
    st.markdown(f"""
    <table class="report-table">
        <tr>
            <th colspan="4" style="text-align: center; font-size: 20px; background-color: #004d40; color: white; padding: 15px;">既有建築能效評估計算書 (BERSe-2024 完整版)</th>
        </tr>
        <tr>
            <td style="font-weight:bold; width:22%; background-color:#fcfcfc;">案件名稱</td>
            <td style="width:28%;">{case_name}</td>
            <td style="font-weight:bold; width:22%; background-color:#fcfcfc;">評估日期</td>
            <td style="width:28%;">2026 年 05 月 25 日</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background-color:#fcfcfc;">地理位置細節</td>
            <td>{case_address} (城鄉分區 {ur_zone} 區)</td>
            <td style="font-weight:bold; background-color:#fcfcfc;">城鄉係數 (UR)</td>
            <td>{ur_value}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background-color:#fcfcfc;">建築大分類</td>
            <td>{selected_category}</td>
            <td style="font-weight:bold; background-color:#fcfcfc;">副分類名稱</td>
            <td>{selected_subcategory}</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background-color:#fcfcfc;">評估樓地板面積 (Ae)</td>
            <td>{floor_area:,.2f} ㎡</td>
            <td style="font-weight:bold; background-color:#fcfcfc;">再生能源扣減度數</td>
            <td>{green_kwh:,.1f} kWh/年</td>
        </tr>
        <tr>
            <td style="font-weight:bold; background-color:#fcfcfc;">年度總用電量</td>
            <td>{total_raw_kwh:,.1f} kWh/年</td>
            <td style="font-weight:bold; background-color:#fcfcfc;">扣減後計算用電量</td>
            <td>{adjusted_kwh:,.1f} kWh/年</td>
        </tr>
        <tr style="background-color: #fcfcfc;">
            <td style="font-weight:bold; color: #004d40;">實際耗電密度 (EUI*)</td>
            <td style="font-weight:bold; color: #004d40; font-size: 15px;">{eui_adjusted:.2f} kWh/㎡·yr</td>
            <td style="font-weight:bold; color: #004d40;">能效得分 (Score_EE)</td>
            <td style="font-weight:bold; color: #004d40; font-size: 15px;">{score:.2f} 分</td>
        </tr>
        <tr style="background-color: #f2fcf5;">
            <td style="font-weight:bold; color: #2e7d32;">基準值三階段指標</td>
            <td style="color: #2e7d32;">EUI_n: {eui_n:.2f} | EUI_g: {eui_g:.2f} | EUI_max: {eui_max:.2f}</td>
            <td style="font-weight:bold; color: #2e7d32;">最終建築能效等級</td>
            <td style="font-weight:bold; color: #2e7d32; font-size: 16px;">{level}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    # 這裡直接用 Markdown 渲染計算推導明細，不再使用帶 HTML 標籤的字串
    st.markdown(detailed_process_markdown)
    
    st.markdown("""
        <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 12px; color: #777;">
            備註：本計算書由 BERSe-2024 動態試算系統自動產生，計算邏輯符合中華民國內政部建築研究所相關規範。
        </div>
    </div>
    """, unsafe_allow_html=True)