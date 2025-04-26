import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64

# 把 ttf 字型讀進來，轉 base64
with open("NotoSansTC-Regular.ttf", "rb") as f:
    font_data = f.read()
base64_font = base64.b64encode(font_data).decode('utf-8')

# 注入 CSS
st.markdown(
    f"""
    <style>
    @font-face {{
        font-family: 'CustomFont';
        src: url(data:font/ttf;base64,{base64_font}) format('truetype');
    }}
    html, body, .main, .css-1v3fvcr, .css-12oz5g7 {{
        font-family: 'CustomFont', sans-serif !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Matplotlib 也設定字型
plt.rcParams['font.family'] = 'Noto Sans TC'

# 讀取CSV
df = pd.read_csv("歷史空氣品質.csv")

# 時間格式處理
df['datacreationdate'] = pd.to_datetime(df['datacreationdate'], errors='coerce')
df['pm2.5'] = pd.to_numeric(df['pm2.5'], errors='coerce')

# 下拉選單：選擇測站
stations = df['sitename'].dropna().unique()
station = st.selectbox('請選擇測站', stations)

# 篩選資料
filtered = df[df['sitename'] == station].sort_values('datacreationdate')

# 畫圖
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(filtered['datacreationdate'], filtered['pm2.5'], marker='o', linestyle='-')
ax.set_title(f"{station} 測站 PM2.5 時間趨勢")
ax.set_xlabel("時間")
ax.set_ylabel("PM2.5 (μg/m³)")
ax.grid(True)
plt.xticks(rotation=45)

# 顯示圖表
st.pyplot(fig)
