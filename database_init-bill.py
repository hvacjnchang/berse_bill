# database_init.py
import sqlite3

def init_database():
    """初始化 SQLite 資料庫，建立資料表並寫入預設數據"""
    conn = sqlite3.connect("berse_2024.db")
    cursor = conn.cursor()
    
    # 建立行政區城鄉係數表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regional_ur (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        county TEXT,
        district TEXT,
        zone TEXT,
        ur_value REAL
    )
    """)
    
    # 建立建築分項中位值參數表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS building_params (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        subcategory TEXT,
        aeui REAL,
        leui REAL,
        eteui REAL,
        hpeui REAL,
        eeui REAL
    )
    """)
    
    # 填入行政區數據 (若空)
    cursor.execute("SELECT COUNT(*) FROM regional_ur")
    if cursor.fetchone()[0] == 0:
        ur_samples = [
            ("台北市", "信義區", "A", 1.0),
            ("台北市", "文山區", "B", 0.95),
            ("新北市", "板橋區", "A", 1.0),
            ("新北市", "雙溪區", "D", 0.7),
            ("台中市", "西屯區", "A", 1.0),
            ("台中市", "和平區", "D", 0.7),
            ("高雄市", "苓雅區", "A", 1.0),
            ("澎湖縣", "馬公市", "C", 0.8)
        ]
        cursor.executemany("INSERT INTO regional_ur (county, district, zone, ur_value) VALUES (?, ?, ?, ?)", ur_samples)
        
    # 填入建築分類中位值 (若空)
    cursor.execute("SELECT COUNT(*) FROM building_params")
    if cursor.fetchone()[0] == 0:
        building_samples = [
            ("辦公類", "大型總部/行政辦公", 50.0, 20.0, 5.0, 0.0, 20.0),
            ("辦公類", "一般中小型辦公", 40.0, 15.0, 3.0, 0.0, 15.0),
            ("百貨商場類", "大型購物中心/百貨", 110.0, 45.0, 10.0, 0.0, 45.0),
            ("百貨商場類", "一般零售商場/量販", 90.0, 35.0, 5.0, 0.0, 35.0),
            ("旅館類", "國際觀光旅館/星級飯店", 80.0, 30.0, 10.0, 30.0, 30.0),
            ("旅館類", "一般商務旅館", 60.0, 25.0, 5.0, 20.0, 25.0)
        ]
        cursor.executemany("INSERT INTO building_params (category, subcategory, aeui, leui, eteui, hpeui, eeui) VALUES (?, ?, ?, ?, ?, ?, ?)", building_samples)
        
    conn.commit()
    conn.close()