import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd

# ==========================================
# 1. 시스템 설정 및 Supabase 연결
# ==========================================
st.set_page_config(page_title="SNS7 CEO 경영관리 시스템", page_icon="💼", layout="wide")

# [필수] 센터장님의 Supabase API 정보로 교체하세요!
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error("데이터베이스 연결에 실패했습니다. URL과 Key를 다시 확인해 주세요.")
    st.stop()

# ==========================================
# 2. 데이터베이스 통신 함수
# ==========================================
def fetch_users():
    """DB에서 유저 계정 정보를 가져옵니다."""
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'name': user['name'],
                'password': user['password'], 
                'role': user['role']
            }
        return credentials
    except Exception as e:
        return {'usernames': {}}

def update_password_in_db(username, hashed_password):
    """비밀번호 변경을 DB에 저장합니다."""
    supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()

# ==========================================
# 3. 로그인 인증 시스템
# ==========================================
credentials = fetch_users()

authenticator = stauth.Authenticate(
    credentials,
    'ceo_portal_cookie', 
    'sns7_secret_key',     
    cookie_expiry_days=30 
)

name, authentication_status, username = authenticator.login('CEO 포털 보안 로그인', 'main')

if authentication_status == False:
    st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
elif authentication_status == None:
    st.info('발급받으신 아이디와 비밀번호를 입력해 주세요.')
    
elif authentication_status == True:
    user_role = credentials['usernames'][username]['role']
    
    # --- 좌측 사이드바 (비밀번호 변경 및 로그아웃) ---
    with st.sidebar:
        st.write(f"**{name}**님 환영합니다.")
        st.divider()
        try:
            if authenticator.reset_password(username, '비밀번호 변경'):
                new_hashed_pw = credentials['usernames'][username]['password']
                update_password_in_db(username, new_hashed_pw)
                st.success('비밀번호가 안전하게 변경되었습니다.')
        except Exception as e:
            st.error("비밀번호 변경 오류")
            
        st.divider()
        authenticator.logout('로그아웃', 'main')

    # ==========================================
    # 4-A. [관리자 모드] 공민준 센터장님 전용
    # ==========================================
    if user_role == 'admin':
        st.title("👑 CEO 포털 통합 관리자 대시보드")
        
        # 전체 데이터 조회
        res = supabase.table('client_data').select('*').execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        else:
            st.info("등록된 고객 데이터가 없습니다.")
        
        st.divider()
        st.subheader("➕ 신규 경영 리포트 등록")
        with st.form("new_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_id = st.text_input("고객 접속 ID")
                c_name = st.text_input("업체명")
            with col2:
                c_score = st.number_input("신용점수", min_value=0, max_value=1000, value=800)
                c_sales = st.number_input("월 매출 (만원)", min_value=0, step=100)
            c_comment = st.text_area("센터장 전략 제언")
            
            if st.form_submit_button("DB에 저장"):
                if c_id and c_name:
                    supabase.table('client_data').insert({
                        'client_id': c_id, 'company_name': c_name,
                        'credit_score': c_score, 'monthly_sales': c_sales,
                        'strategy_comment': c_comment
                    }).execute()
                    st.success("성공적으로 발행되었습니다! (새로고침을 눌러주세요)")
                else:
                    st.warning("고객 ID와 업체명은 필수입니다.")

    # ==========================================
    # 4-B. [고객 모드] 업체 사장님 전용
    # ==========================================
    else:
        st.title(f"📈 {name} 전용 경영 리포트")
        
        # 본인 데이터만 필터링해서 가져오기
        res = supabase.table('client_data').select('*').eq('client_id', username).execute()
        
        if res.data:
            user_data = res.data[0] 
            col1, col2, col3 = st.columns(3)
            col1.metric("업체명", user_data['company_name'])
            col2.metric("현재 신용점수", f"{user_data['credit_score']} 점")
            col3.metric("최근 월 매출", f"{user_data['monthly_sales']:,} 만원")
            
            st.divider()
            st.subheader("💡 공민준 센터장의 맞춤 전략")
            st.info(user_data['strategy_comment'])
        else:
            st.warning("아직 발행된 리포트가 없습니다. 센터장에게 문의해 주세요.")
