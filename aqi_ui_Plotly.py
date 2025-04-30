import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import math

st.set_page_config(
    page_title='台灣空氣品質儀表板',
    page_icon='🌫️',
)

st.title('🌫️ 台灣空氣品質儀表板')

# -------------------------------------------------------------------
# 讀取資料

@st.cache_data(ttl=3600)
def get_air_quality_data():
    # 最新空氣品質資料
    current_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=9e565f9a-84dd-4e79-9097-d403cae1ea75&limit=1000&sort=ImportDate desc&format=JSON'
    # 歷史空氣品質資料
    history_url = 'https://data.moenv.gov.tw/api/v2/aqx_p_488?api_key=9b651a1b-0732-418e-b4e9-e784417cadef&limit=1000&sort=datacreationdate desc&format=JSON'

    try:
        cur_res = requests.get(current_url)
        cur_res.raise_for_status()  # 如果回應的狀態碼不是 200，會觸發異常
        cur_res_json = cur_res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"無法獲取當前空氣品質資料: {e}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        his_res = requests.get(history_url)
        his_res.raise_for_status()
        his_res_json = his_res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"無法獲取歷史空氣品質資料: {e}")
        return pd.DataFrame(), pd.DataFrame()

    current_df = pd.DataFrame(cur_res_json['records'])
    history_df = pd.DataFrame(his_res_json['records'])

    # 格式化欄位
    for df in [current_df, history_df]:
        df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')
        df['datacreationdate'] = pd.to_datetime(df['datacreationdate'], errors='coerce')

    return current_df, history_df

current_df, history_df = get_air_quality_data()

# -------------------------------------------------------------------
# 使用者選擇

counties = sorted(current_df['county'].dropna().unique())
selected_counties = st.multiselect('選擇縣市', counties, default=['臺北市', '高雄市'])

stations = current_df[current_df['county'].isin(selected_counties)]['sitename'].unique()
selected_stations = st.multiselect('選擇測站', stations, default=stations[:5])

# 篩選歷史資料
filtered_history = history_df[
    (history_df['sitename'].isin(selected_stations))
    & (history_df['county'].isin(selected_counties))
].copy()

# -------------------------------------------------------------------
# 圖表呈現

st.header('📈 AQI 變化趨勢（歷史）', divider='gray')
if filtered_history.empty:
    st.warning('查無歷史資料，請更換選項')
else:
    st.line_chart(
        filtered_history,
        x='datacreationdate',
        y='aqi',
        color='sitename'
    )

# -------------------------------------------------------------------
# 顯示最新 AQI 值 + 變化量

st.header('📊 最新 AQI 狀況', divider='gray')

cols = st.columns(4)

for i, site in enumerate(selected_stations):
    col = cols[i % len(cols)]
    with col:
        current_aqi = current_df[current_df['sitename'] == site]['aqi'].values
        if len(current_aqi) == 0 or math.isnan(current_aqi[0]):
            st.metric(label=site, value='n/a')
        else:
            now = current_aqi[0]

            # 嘗試找歷史資料中的上一筆該站 AQI 值
            past = history_df[history_df['sitename'] == site].sort_values('datacreationdate', ascending=False)
            if len(past) > 1:
                prev_aqi = past.iloc[1]['aqi']
                delta = now - prev_aqi if pd.notna(prev_aqi) else 0
            else:
                delta = 0

            st.metric(
                label=site,
                value=f"{now:.0f}",
                delta=f"{delta:+.0f}"
            )
