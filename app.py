import streamlit as st
from supabase import create_client
import plotly.express as px
import pandas as pd

# 1. 환경 설정
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("설정 오류: Secrets 설정을 확인해주세요.")

# 2. 페이지 설정
st.set_page_config(page_title="SNS7 경영지원 포털", layout="wide")

def main():
    if "user" not in st.session_state:
        show_login_page()
    else:
        show_dashboard()

# 3. 로그인 페이지 (데모 버튼 추가)
def show_login_page():
    st.title("💼 SNS7 경영지원 통합관리 포털")
    st.write("대표님의 경영 현황을 실시간 데이터로 확인하세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("카카오톡으로 시작하기 (연동 전)"):
            st.info("카카오 로그인 설정이 필요합니다.")
            
    with col2:
        # 이 버튼을 누르면 로그인 없이 바로 대시보드로 들어갑니다.
        if st.button("🏠 데모 버전으로 바로 들어가기"):
            st.session_state.user = {"name": "민준", "id": "1"}
            st.rerun()

# 4. 대시보드 화면
def show_dashboard():
    user = st.session_state.user
    st.sidebar.title(f"👋 {user['name']} 대표님")
    
    if st.sidebar.button("로그아웃"):
        del st.session_state.user
        st.rerun()

    menu = st.sidebar.selectbox("메뉴", ["📊 경영 대시보드", "🔍 정책자금 분석"])

    if menu == "📊 경영 대시보드":
        st.header("📈 실시간 경영 분석 리포트")
        
        # 금고에서 데이터 가져오기 시도
        try:
            res = supabase.table("financial_data").select("*").eq("user_id", user['id']).execute()
            data = res.data
            
            if not data: # 데이터가 없으면 샘플 보여주기
                st.warning("금고에 아직 데이터가 없습니다. 샘플 데이터를 표시합니다.")
                data = [
                    {"date": "2026-04", "credit_score": 720, "saved_amount": 350000},
                    {"date": "2026-05", "credit_score": 745, "saved_amount": 480000},
                    {"date": "2026-06", "credit_score": 780, "saved_amount": 620000}
                ]
            
            df = pd.DataFrame(data)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("신용점수 추이")
                fig = px.line(df, x="date", y="credit_score", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("예상 절감액")
                fig2 = px.bar(df, x="date", y="saved_amount", color="date")
                st.plotly_chart(fig2, use_container_width=True)
        except:
            st.error("데이터를 불러오는 중 오류가 발생했습니다. SQL Editor에서 테이블을 만드셨나요?")

if __name__ == "__main__":
    main()
