import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# 1. 로봇의 열쇠 꾸러미
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 2. 웹사이트 명품 테마 설정
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- [수정된 부분] 커스텀 스타일 (CSS) 적용 ---
st.markdown("""
<style>
    /* 배경색: 연한 그레이 블루 (세련된 느낌) */
    .stApp {
        background-color: #F8FAFC; 
    }
    
    /* 사이드바: 짙은 네이비 */
    [data-testid="stSidebar"] {
        background-color: #1E3A8A !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* 제목 색상: 짙은 네이비 */
    h1, h2, h3 {
        color: #1E3A8A !important;
        font-family: 'Pretendard', sans-serif;
    }

    /* 버튼: 반짝이는 골드 포인트 */
    .stButton>button {
        background-color: #DAA520 !important;
        color: white !important;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True) # <-- 이 부분이 수정되었습니다!

# 3. 메인 화면 구성
st.title("📊 SNS7 경영지원 실시간 리포트")
st.write(f"### **민준 대표님**, 환영합니다! 현재 경영 상태를 분석했습니다.")
st.divider()

# 4. 데이터 가져오기 및 그래프 그리기
try:
    res = supabase.table("financial_data").select("*").execute()
    data = res.data

    if data:
        df = pd.DataFrame(data).sort_values(by="date")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 신용점수 변화")
            # 골드 색상 적용
            fig_credit = px.line(df, x="date", y="credit_score", 
                                 markers=True, text="credit_score",
                                 color_discrete_sequence=["#DAA520"])
            fig_credit.update_traces(textposition="top center", line=dict(width=4))
            fig_credit.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_credit, use_container_width=True)

        with col2:
            st.subheader("💰 예상 절감액 (누적)")
            # 골드 색상 적용
            fig_saved = px.bar(df, x="date", y="saved_amount", 
                               text_auto=True,
                               color_discrete_sequence=["#DAA520"])
            fig_saved.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_saved, use_container_width=True)

        st.divider()
        st.subheader("📋 상세 데이터 확인")
        st.dataframe(df[['date', 'credit_score', 'saved_amount']], use_container_width=True)

    else:
        st.warning("금고에 아직 보물이 없어요!")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

# 5. 사이드바 관리 메뉴
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    if st.button("🔄 데이터 새로고침"):
        st.rerun()
