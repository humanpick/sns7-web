import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"데이터베이스 연결 실패: {e}")
    st.stop()

# ==========================================
# 2. 데이터베이스 통신 함수 (이메일 꼼수 추가)
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'email': f"{user['username']}@ceo.com", # [해결 1] 라이브러리 에러 방지용 가짜 이메일 자동 부여
                'name': user['name'],
                'password': user['password'],
                'role': user['role']
            }
        return credentials
    except Exception as e:
        return {'usernames': {}}

def update_password_in_db(username, hashed_password):
    supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()

# ==========================================
# 🛠️ [해결 2] 비밀번호 강제 동기화 마스터 버튼
# ==========================================
if st.button("🚨 [여기를 클릭하세요] 관리자 비밀번호 '1234'로 서버 맞춤 동기화"):
    import bcrypt  # 파이썬 순정 암호화 엔진 호출
    
    # 1234를 서버에 완벽하게 맞는 해시 암호로 직접 변환
    new_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    update_password_in_db('admin_gong', new_hash)
    
    st.success("✅ 서버 맞춤형 암호화가 Supabase에 적용되었습니다! 이제 키보드의 F5(새로고침)를 누르고 로그인해 보세요.")
    st.stop()

# ==========================================
# 3. 로그인 및 인증 시스템
# ==========================================
credentials = fetch_users()

authenticator = stauth.Authenticate(
    credentials,
    'ceo_portal_cookie', 
    'signature_key',     
    cookie_expiry_days=30 
)

authenticator.login('main')

if st.session_state["authentication_status"] == False:
    st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
elif st.session_state["authentication_status"] == None:
    st.info('발급받으신 아이디와 비밀번호를 입력해 주세요.')
    
elif st.session_state["authentication_status"] == True:
    
    username = st.session_state["username"]
    name = st.session_state["name"]
    user_role = credentials['usernames'][username]['role']
    
    with st.sidebar:
        st.write(f"**{name}**님 반갑습니다.")
        st.divider()
        try:
            if authenticator.reset_password(username, 'sidebar'):
                new_hashed_pw = credentials['usernames'][username]['password']
                update_password_in_db(username, new_hashed_pw)
                st.success('비밀번호가 안전하게 변경되었습니다.')
        except Exception as e:
            st.error(f"비밀번호 변경 중 오류: {e}")
        st.divider()
        authenticator.logout('로그아웃', 'sidebar')

    # [관리자 대시보드]
    if user_role == 'admin':
        st.title("👑 CEO 포털 통합 관리자 대시보드")
        
        try:
            res = supabase.table('client_data').select('*').execute()
            if res.data:
                all_df = pd.DataFrame(res.data)
                st.dataframe(all_df, use_container_width=True, hide_index=True)
            else:
                st.info("등록된 고객 데이터가 없습니다.")
        except:
            st.warning("⚠️ 'client_data' 테이블을 생성해야 데이터를 불러올 수 있습니다.")
        
        st.divider()
        st.subheader("➕ 신규 경영 리포트 발행")
        with st.form("new_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_id = st.text_input("고객 ID", placeholder="예: client_kim")
                c_name = st.text_input("업체명", placeholder="예: (주)인슈테크")
            with col2:
                c_score = st.number_input("신용점수", min_value=0, max_value=1000, value=850)
                c_sales = st.number_input("월 매출 (만원 단위)", min_value=0, step=100)
            c_comment = st.text_area("센터장님 전용 전략 코멘트")
            
            if st.form_submit_button("DB 저장"):
                if c_id and c_name:
                    supabase.table('client_data').insert({
                        'client_id': c_id, 'company_name': c_name,
                        'credit_score': c_score, 'monthly_sales': c_sales,
                        'strategy_comment': c_comment
                    }).execute()
                    st.success("저장 완료!")
                    st.rerun()

    # [고객 대시보드]
    else:
        st.title(f"📈 {name} 대표님 맞춤형 경영 대시보드")
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            if res.data:
                user_data = res.data[0] 
                col1, col2, col3 = st.columns(3)
                col1.metric("업체명", user_data['company_name'])
                col2.metric("현재 신용점수", f"{user_data['credit_score']} 점")
                col3.metric("최근 월 매출", f"{user_data['monthly_sales']:,} 만원")
                st.divider()
                st.info(user_data['strategy_comment'])
            else:
                st.warning("발행된 리포트가 없습니다.")
        except:
             st.warning("데이터베이스 연동 중입니다.")
