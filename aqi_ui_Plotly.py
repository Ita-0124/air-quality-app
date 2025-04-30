import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="台灣空氣品質儀表板", layout="wide")
st.title("🌫️ 台灣空氣品質即時與歷史資料儀表板")

# ----------- 更新資料按鈕功能 -----------
if st.button("🔄 更新資料"):
    st.cache_data.clear()  # 清除快取資料
    st.experimental_rerun()

# ----------- 資料讀取與快取 -----------
@st.cache_data(ttl=3600)
def get_air_quality_data():
    current_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=ImportDate desc&format=JSON'
    history_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_488?api_key=9b651a1b-0732-418e-b4e9-e784417cadef&limit=1000&sort=datacreationdate desc&format=JSON'

    cur_res = requests.get(current_url).json()
    his_res = requests.get(history_url).json()

    current_df = pd.DataFrame(cur_res['records'])
    history_df = pd.DataFrame(his_res['records'])

    # 統一時間與數值格式
    current_df['aqi'] = pd.to_numeric(current_df['aqi'], errors='coerce')
    current_df['publishtime'] = pd.to_datetime(current_df['publishtime'], errors='coerce')
    current_df['datetime'] = current_df['publishtime']  # 統一時間欄位

    history_df['aqi'] = pd.to_numeric(history_df['aqi'], errors='coerce')
    history_df['datacreationdate'] = pd.to_datetime(history_df['datacreationdate'], errors='coerce')
    history_df['datetime'] = history_df['datacreationdate']  # 統一時間欄位

    return current_df, history_df

# 定義 session_state 來追蹤是否要強制重新抓取資料
if "refresh_data" not in st.session_state:
    st.session_state["refresh_data"] = False
if "last_update_time" not in st.session_state:
    st.session_state["last_update_time"] = None

# 排成一列：按鈕 + 更新時間
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 更新資料"):
        st.session_state["refresh_data"] = True

with col2:
    if st.session_state["last_update_time"]:
        st.markdown(f"🕒 最後更新時間：{st.session_state['last_update_time'].strftime('%Y-%m-%d %H:%M:%S')}")

# -------------------------------------------------------------------
# 讀取資料（加上按鈕控制是否強制重新下載）

@st.cache_data(ttl=3600)
def get_air_quality_data():
    current_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=9e565f9a-84dd-4e79-9097-d403cae1ea75&limit=1000&sort=ImportDate desc&format=JSON'
    history_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_488?api_key=9b651a1b-0732-418e-b4e9-e784417cadef&limit=1000&sort=datacreationdate desc&format=JSON'

    cur_res = requests.get(current_url).json()
    his_res = requests.get(history_url).json()

    current_df = pd.DataFrame(cur_res['records'])
    history_df = pd.DataFrame(his_res['records'])

    for df in [current_df, history_df]:
        df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')

    if 'datacreationdate' in history_df.columns:
        history_df['datacreationdate'] = pd.to_datetime(history_df['datacreationdate'], errors='coerce')
    if 'publishtime' in current_df.columns:
        current_df['publishtime'] = pd.to_datetime(current_df['publishtime'], errors='coerce')

    return current_df, history_df

# 如果按下更新或第一次載入，重新抓資料
if st.session_state["refresh_data"] or "current_df" not in st.session_state:
    current_df, history_df = get_air_quality_data()
    st.session_state["current_df"] = current_df
    st.session_state["history_df"] = history_df
    st.session_state["last_update_time"] = datetime.now()
    st.session_state["refresh_data"] = False
else:
    current_df = st.session_state["current_df"]
    history_df = st.session_state["history_df"]

# ----------- 讀取資料 -----------
current_df, history_df = get_air_quality_data()

# ----------- 使用者選單 -----------
counties = sorted(current_df['county'].dropna().unique())
selected_county = st.selectbox("請選擇縣市", counties)

site_names = current_df[current_df['county'] == selected_county]['sitename'].unique()
selected_site = st.selectbox("請選擇測站", site_names)

# ----------- 資料篩選 -----------
site_current_data = current_df[(current_df['county'] == selected_county) & (current_df['sitename'] == selected_site)]
site_history_data = history_df[(history_df['county'] == selected_county) & (history_df['sitename'] == selected_site)]

# ----------- 畫圖區塊 -----------
st.subheader(f"📍 {selected_county} - {selected_site} 空氣品質趨勢圖")

fig = px.line(
    site_history_data.sort_values("datetime"),
    x="datetime", y="aqi",
    title="AQI 指數變化",
    labels={"datetime": "時間", "aqi": "AQI"},
    markers=True
)
st.plotly_chart(fig, use_container_width=True)

# ----------- 即時數據顯示 -----------
st.subheader("📊 即時空氣品質數據")
if not site_current_data.empty:
    st.dataframe(site_current_data.set_index("sitename")[["aqi", "status", "pm2.5", "pm10", "o3", "co", "so2", "no2"]])
else:
    st.warning("⚠️ 查無即時數據。")
