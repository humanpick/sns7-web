import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# 1. 로봇의 열쇠 꾸러미 (수정 금지)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 2. 웹사이트 예쁘게 꾸미기
st.set_page_config(page_title="SNS7 CEO 포털", layout="wide")

st.title("📊 SNS7 경영지원 실시간 리포트")
st.write(f"### **민준 대표님**, 환영합니다! 현재 경영 상태를 분석했습니다.")

# 3. 보물상자에서 데이터 꺼내오기
try:
    res = supabase.table("financial_data").select("*").execute()
    data = res.data

    if data:
        # 데이터 뭉치(JSON)를 표(DataFrame)로 변환하기
        df = pd.DataFrame(data)
        
        # 날짜순으로 정렬 (혹시 순서가 섞여있을까봐요!)
        df = df.sort_values(by="date")

        # 화면을 반으로 나눠서 그래프 두 개 그리기
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 신용점수 변화")
            # 선 그래프 그리기
            fig_credit = px.line(df, x="date", y="credit_score", 
                                 markers=True, text="credit_score",
                                 color_discrete_sequence=["#FF4B4B"])
            fig_credit.update_traces(textposition="top center")
            st.plotly_chart(fig_credit, use_container_width=True)

        with col2:
            st.subheader("💰 예상 절감액 (누적)")
            # 막대 그래프 그리기
            fig_saved = px.bar(df, x="date", y="saved_amount", 
                               text_auto=True,
                               color_discrete_sequence=["#00CC96"])
            st.plotly_chart(fig_saved, use_container_width=True)

        # 아래쪽에 상세 표 보여주기
        st.divider()
        st.subheader("📋 상세 데이터 확인")
        st.table(df[['date', 'credit_score', 'saved_amount']])

    else:
        st.warning("상자에 보물은 있는데 내용물이 비어있어요!")

except Exception as e:
    st.error(f"로봇이 그림을 그리다가 실수했어요: {e}")

# 4. 로그아웃 버튼 (나중에 쓸 거예요)
if st.sidebar.button("데이터 새로고침"):
    st.rerun()
