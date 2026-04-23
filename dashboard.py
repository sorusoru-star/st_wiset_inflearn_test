import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.collect_data import NaverApiWrapper
import os

# 페이지 설정
st.set_page_config(page_title="Naver API Market Dashboard", layout="wide")

# 사이드바 메뉴 구성
st.sidebar.title("📊 통합 분석 메뉴")
menu = st.sidebar.radio(
    "보고서 선택",
    ["홈/요약", "트렌드 상세", "판매 실적 분석", "커뮤니티/뉴스"]
)

st.sidebar.markdown("---")
keywords_raw = st.sidebar.text_input("검색어 (콤마 구분)", value="핫팩, 선풍기")
keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

# API 설정 로드
client_id = os.getenv("NAVER_CLIENT_ID", "")
client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

# --- Helper for API ---
def get_api_wrapper():
    return NaverApiWrapper(client_id, client_secret)

# 데이터 수집 버튼
if st.sidebar.button("🚀 데이터 업데이트 시작"):
    if not client_id or not client_secret:
        st.sidebar.error("API 키가 없습니다. .env 파일을 확인해 주세요.")
    else:
        with st.spinner("네이버 데이터를 분석 중입니다..."):
            api = get_api_wrapper()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            # Fetch data
            try:
                st.session_state.data = api.collect_all(keywords, start_date, end_date)
                st.session_state.logs = api.status_logs
                st.success("분석 완료!")
            except Exception as e:
                st.error(f"데이터 수집 중 오류 발생: {e}")

# 메인 화면 구성
if 'data' not in st.session_state:
    st.header("🏠 네이버 데이터 분석 대시보드")
    st.info("왼쪽 메뉴에서 '데이터 업데이트 시작' 버튼을 눌러 실시간 분석을 시작해 주세요.")
    st.markdown("""
    ### 분석 가능한 항목:
    - **트렌드**: 검색량 변화 추이 분석
    - **판매 실적**: 상품별 판매수 및 리뷰 지수
    - **브랜드**: 시장 내 브랜드 점유율
    - **커뮤니티**: 블로그, 뉴스 실시간 반응
    """)
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=80", caption="Data Analysis Dashboard Waiting...")
else:
    data = st.session_state.data
    
    if menu == "홈/요약":
        st.header("🏢 시장 통합 분석 요약")
        c1, c2, c3 = st.columns(3)
        c1.metric("검색어", ", ".join(keywords))
        
        if not data['shop'].empty:
            shop_df = data['shop'].copy()
            shop_df['lprice'] = pd.to_numeric(shop_df['lprice'], errors='coerce')
            c2.metric("평균 가격", f"{int(shop_df['lprice'].dropna().mean()):,}원")
            try:
                top_brand = shop_df['brand'].mode()[0] if not shop_df['brand'].empty else "N/A"
                c3.metric("최고 인기 브랜드", top_brand)
            except:
                c3.metric("최고 인기 브랜드", "N/A")

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(shop_df, names='brand', title="브랜드 점유율")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.histogram(shop_df, x="lprice", title="가격대 분포")
                st.plotly_chart(fig2, use_container_width=True)

    elif menu == "트렌드 상세":
        st.header("📈 검색어 트렌드 추이")
        if not data['trend'].empty:
            fig = px.line(data['trend'], title="최근 1년 검색지수 변화")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("트렌드 데이터가 없습니다.")

    elif menu == "판매 실적 분석":
        st.header("💰 판매 지수 분석")
        if not data['shop'].empty:
            shop_df = data['shop'].copy()
            shop_df['lprice'] = pd.to_numeric(shop_df['lprice'], errors='coerce')
            # Use sales_count if available (from our updated collector)
            y_axis = 'sales_count' if 'sales_count' in shop_df.columns else 'lprice'
            fig = px.scatter(shop_df, x="lprice", y=y_axis, 
                             size="review_count" if 'review_count' in shop_df.columns else None, 
                             color="search_keyword", hover_name="title",
                             title=f"가격 대비 {y_axis} 분석")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("🏆 상품 상세 리스트")
            st.dataframe(shop_df)
        else:
            st.warning("분석할 쇼핑 데이터가 없습니다.")

    elif menu == "커뮤니티/뉴스":
        st.header("🗣 소셜 미디어 분석")
        tab1, tab2, tab3 = st.tabs(["뉴스", "블로그", "카페"])
        with tab1: st.dataframe(data['news'])
        with tab2: st.dataframe(data['blog'])
        with tab3: st.dataframe(data['cafearticle'])
