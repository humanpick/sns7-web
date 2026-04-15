import streamlit as st
from supabase import create_client
import plotly.express as px
import pandas as pd

# 1. 환경 설정 (Supabase 연동)
# Streamlit Cloud의 Settings -> Secrets에 아래 정보가 입력되어야 합니다.
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("설정 오류: Supabase URL 또는 Key가 Secrets에 설정되지 않았습니다.")

# 2. 페이지 설정 및 레이아웃
st.set_page_config(page_title="SNS7 경영지원 CEO 포털", layout="wide")

def main():
    # 간단한 세션 상태 관리 (로그인 여부)
    if "user" not in st.session_state:
        show_login_page()
    else:
        show_dashboard()

# 3. 로그인 페이지 (카카오 로그인 연동)
def show_login_page():
    st.title("💼 SNS7 경영지원 통합관리 포털")
    st.write("대표님의 경영 현황을 실시간 데이터로 확인하세요.")
    
    if st.button("카카오톡으로 1초 만에 시작하기"):
        # 실제 운영 시 redirect_to 주소를 sns7.kr 도메인으로 변경해야 합니다.
        try:
            res = supabase.auth.sign_in_with_oauth({
                "provider": "kakao",
                "options": {"redirect_to": "https://sns7-ceo.streamlit.app"}
            })
            st.info("로그인 페이지로 이동 중...")
        except:
            st.warning("로그인 기능을 활성화하려면 Supabase 설정이 필요합니다.")

# 4. 경영 정보 대시보드
def show_dashboard():
    # 샘플 사용자 정보 (DB 연동 전 임시 데이터)
    user_name = "민준" 
    st.sidebar.title(f"👋 {user_name} 대표님")
    
    menu = st.sidebar.selectbox("메뉴 선택", ["📊 경영 대시보드", "🔍 정책자금 분석", "📋 신청 현황"])

    if menu == "📊 경영 대시보드":
        st.header("📈 실시간 경영 분석 리포트")
        
        # 샘플 데이터 호출
        data = fetch_financial_data(1)
        df = pd.DataFrame(data)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("신용점수 추이")
            fig_credit = px.line(df, x="date", y="credit_score", markers=True, title="월별 신용점수 변화")
            st.plotly_chart(fig_credit, use_container_width=True)
            
        with col2:
            st.subheader("예상 비용 절감액")
            fig_fee = px.bar(df, x="date", y="saved_amount", color="date", title="누적 절감 혜택")
            st.plotly_chart(fig_fee, use_container_width=True)

    elif menu == "🔍 정책자금 분석":
        st.subheader("🔎 기업 맞춤 정책자금 매칭")
        st.info("대표님의 현재 재무 상태를 바탕으로 가장 유리한 자금을 분석 중입니다.")

# 5. 데이터 불러오기 함수 (DB 연동 샘플)
def fetch_financial_data(user_id):
    # 나중에 실제 DB에서 가져올 데이터입니다.
    return [
        {"date": "2026-01", "credit_score": 633, "saved_amount": 0},
        {"date": "2026-02", "credit_score": 650, "saved_amount": 120000},
        {"date": "2026-03", "credit_score": 685, "saved_amount": 250000},
    ]

if __name__ == "__main__":
    main()