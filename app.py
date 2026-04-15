import streamlit as st
from supabase import create_client
import plotly.express as px
import pandas as pd

# 1. 환경 설정 (Supabase 연동)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 2. 페이지 설정 및 사이드바
st.set_page_config(page_title="민준 컨설팅 CEO 포털", layout="wide")

def main():
    if "user" not in st.session_state:
        show_login_page()
    else:
        show_dashboard()

# 3. 카카오 로그인 페이지
def show_login_page():
    st.title("?? 민준 컨설팅 경영지원 포털")
    st.write("사장님의 재무 건강을 숫자로 확인하세요.")
    
    if st.button("카카오로 1초 만에 시작하기"):
        # Supabase를 통한 카카오 OAuth 인증 호출
        res = supabase.auth.sign_in_with_oauth({
            "provider": "kakao",
            "options": {"redirect_to": "https://your-domain.com"}
        })
        st.write("로그인 페이지로 이동 중...")

# 4. 고객 전용 대시보드 (핵심 기능)
def show_dashboard():
    user = st.session_state.user
    st.sidebar.title(f"?? {user['name']} 사장님")
    
    menu = st.sidebar.selectbox("메뉴 선택", ["재무 대시보드", "보험 리모델링", "자금 신청 현황"])

    if menu == "재무 대시보드":
        st.header("?? 나의 재무 개선 추이")
        
        # DB에서 데이터 불러오기 (예시 데이터)
        data = fetch_financial_data(user['id'])
        df = pd.DataFrame(data)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("신용점수 변화")
            fig_credit = px.line(df, x="date", y="credit_score", markers=True)
            st.plotly_chart(fig_credit, use_container_width=True)
            
        with col2:
            st.subheader("월 고정 지출 절감액")
            fig_fee = px.bar(df, x="date", y="saved_amount", color="date")
            st.plotly_chart(fig_fee, use_container_width=True)

    elif menu == "보험 리모델링":
        st.subheader("?? 가입 보험 분석 결과")
        st.info("현재 분석된 리포트가 1건 있습니다. 확인 버튼을 눌러주세요.")

# 5. 데이터 불러오기 함수 (추후 DB 연결)
def fetch_financial_data(user_id):
    # 실제 운영 시 supabase.table("financial_data").select("*").eq("user_id", user_id).execute() 사용
    return [
        {"date": "2026-01", "credit_score": 633, "saved_amount": 0},
        {"date": "2026-02", "credit_score": 650, "saved_amount": 120000},
        {"date": "2026-03", "credit_score": 685, "saved_amount": 250000},
    ]

if __name__ == "__main__":
    main()