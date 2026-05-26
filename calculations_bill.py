# calculations.py

def calculate_benchmarks(ur_value, aeui, leui, eteui, hpeui, eeui):
    """依據城鄉係數及分項中位值計算 2024版能效三大基準"""
    eui_n = ur_value * (0.5 * (aeui + leui + eteui + hpeui) + eeui)
    eui_g = ur_value * (0.8 * (aeui + leui + eteui + hpeui) + eeui)
    eui_max = ur_value * (2.0 * (aeui + leui + eteui + hpeui) + eeui)
    return eui_n, eui_g, eui_max

def calculate_score_and_level(user_eui, eui_n, eui_g, eui_max):
    """計算 BERS 得分與對應分級"""
    if user_eui <= eui_g:
        score = 50 + 40 * ((eui_g - user_eui) / (eui_g - eui_n))
        score = min(100.0, score)  # 上限 100 分
    else:
        score = 50 * ((eui_max - user_eui) / (eui_max - eui_g))
        score = max(0.0, score)    # 下限 0 分
        
    # 分級判定
    if score >= 90:
        level = "1+ 級 (近零碳建築)"
        css_class = "level-1plus"
    elif score >= 80:
        level = "1 級"
        css_class = "level-1"
    elif score >= 70:
        level = "2 級"
        css_class = "level-2"
    elif score >= 60:
        level = "3 級"
        css_class = "level-3"
    elif score >= 50:
        level = "4 級"
        css_class = "level-4"
    elif score >= 40:
        level = "5 級"
        css_class = "level-5"
    elif score >= 20:
        level = "6 級"
        css_class = "level-6"
    else:
        level = "7 級"
        css_class = "level-7"
        
    return score, level, css_class

def generate_detailed_process(ur_value, aeui, leui, eteui, hpeui, eeui, total_raw_kwh, green_kwh, floor_area, eui_adjusted, eui_n, eui_g, eui_max, score, level):
    """生成符合查驗規範的詳細計算過程說明 (採用純 Markdown 與 LaTeX 數學公式)"""
    
    eui_raw = total_raw_kwh / floor_area
    sum_eui = aeui + leui + eteui + hpeui
    
    # 判定得分公式類型與代入式
    if eui_adjusted <= eui_g:
        formula_text = "**[優良級公式]** $SCORE_{EE} = 50 + 40 \\times \\frac{EUI_g - EUI^*}{EUI_g - EUI_n}$"
        substitution_text = f"SCORE_{{EE}} = 50 + 40 \\times \\frac{{{eui_g:.2f} - {eui_adjusted:.2f}}}{{{eui_g:.2f} - {eui_n:.2f}}}"
    else:
        formula_text = "**[不良級公式]** $SCORE_{EE} = 50 \\times \\frac{EUI_{max} - EUI^*}{EUI_{max} - EUI_g}$"
        substitution_text = f"SCORE_{{EE}} = 50 \\times \\frac{{{eui_max:.2f} - {eui_adjusted:.2f}}}{{{eui_max:.2f} - {eui_g:.2f}}}"

    markdown_text = f"""
### 📝 建築能效等級動態計算過程明細

**【步驟一：確認城鄉係數 (UR)】**
本案行政區對應之城鄉分區係數：**UR = {ur_value}**

**【步驟二：取得建築用途分項耗能中位值】**
依手冊基準值，各分項數值如下：
* 空調中位值 (AEUI) = **{aeui}** kWh/㎡·yr
* 照明中位值 (LEUI) = **{leui}** kWh/㎡·yr
* 電梯中位值 (EtEUI) = **{eteui}** kWh/㎡·yr
* 熱水中位值 (HpEUI) = **{hpeui}** kWh/㎡·yr
* 電器基準值 (EEUI) = **{eeui}** kWh/㎡·yr

**【步驟三：計算三大能效指標基準值】**
分項中位值總和 (AEUI + LEUI + EtEUI + HpEUI) = {aeui} + {leui} + {eteui} + {hpeui} = **{sum_eui}** kWh/㎡·yr

1. **近零碳基準 (EUI_n)** = UR × [0.5 × (分項中位值總和) + EEUI]
   $$\\Rightarrow {ur_value} \\times [0.5 \\times {sum_eui} + {eeui}] = \\mathbf{{{eui_n:.2f}}}\\text{{ kWh/㎡·yr}}$$
2. **綠建築基準 (EUI_g)** = UR × [0.8 × (分項中位值總和) + EEUI]
   $$\\Rightarrow {ur_value} \\times [0.8 \\times {sum_eui} + {eeui}] = \\mathbf{{{eui_g:.2f}}}\\text{{ kWh/㎡·yr}}$$
3. **限制值基準 (EUI_max)** = UR × [2.0 × (分項中位值總和) + EEUI]
   $$\\Rightarrow {ur_value} \\times [2.0 \\times {sum_eui} + {eeui}] = \\mathbf{{{eui_max:.2f}}}\\text{{ kWh/㎡·yr}}$$

**【步驟四：計算實際耗電密度指標 (EUI*)】**
* 年度用電總量：**{total_raw_kwh:,.1f}** kWh/年
* 再生能源扣減額度：**{green_kwh:,.1f}** kWh/年
* 扣減後計算用電量：{total_raw_kwh:,.1f} - {green_kwh:,.1f} = **{total_raw_kwh - green_kwh:,.1f}** kWh/年
* 評估樓地板面積 (Ae)：**{floor_area:,.2f}** ㎡
* 實際耗電密度：
  $$EUI^* = \\frac{{{total_raw_kwh - green_kwh:.1f}}}{{{floor_area:.2f}}} = \\mathbf{{{eui_adjusted:.2f}}}\\text{{ kWh/㎡·yr}}$$ (原始 EUI*：{eui_raw:.2f})

**【步驟五：計算能效總得分 (SCORE_EE)】**
* 套用公式：{formula_text}
* 數值代入：
  $${substitution_text} = \\mathbf{{{score:.2f}}}\\text{{ 分}}$$

**【步驟六：判定能效等級】**
對照 2024 年版 BERS 分級表，本案能效總得分為 **{score:.2f}** 分，最終判定等級為 **{level}**。
"""
    return markdown_text