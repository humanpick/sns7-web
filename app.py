import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# [필수] 센터장님의 Supabase 정보를 입력하세요. (따옴표 유지)
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "여기에_복사하신_긴_anon_public_key를_넣으세요"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"데이터베이스 연결 실패: {e}")
    st.stop()

# ==========================================
# 2. 데이터베이스 통신 함수
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'email': f"{user['username']}@ceo.com", 
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

    # ==========================================
    # 4-A. [관리자 모드] 공민준 센터장 전용 
    # ==========================================
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
        st.subheader("➕ 신규 경영 리포트 발행 및 계정 자동 생성")
        with st.form("new_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_id = st.text_input("고객 ID", placeholder="예: client_kim")
                c_name = st.text_input("업체명", placeholder="예: (주)인슈테크")
            with col2:
                c_score = st.number_input("신용점수", min_value=0, max_value=1000, value=850)
                c_sales = 리포트 = st.number_input("월 매출 (만원 단위)", min_value=0, step=100)
            c_comment = st.text_area("센터장님 전용 전략 코멘트")
            
            if st.form_submit_button("DB 저장 및 계정 생성"):
                if c_id and c_name:
                    try:
                        # 1. users 테이블에 계정 자동 생성 (초기 비밀번호 1234)
                        temp_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        supabase.table('users').upsert({
                            'username': c_id, 
                            'password': temp_hash,
                            'name': c_name,
                            'role': 'client'
                        }).execute()

                        # 2. client_data 테이블에 리포트 저장
                        supabase.table('client_data').upsert({
                            'client_id': c_id, 
                            'company_name': c_name,
                            'credit_score': c_score, 
                            'monthly_sales': c_sales,
                            'strategy_comment': c_comment
                        }).execute()

                        st.success(f"✅ [{c_name}] 대표님의 데이터 저장 및 로그인 계정(초기 비밀번호: 1234)이 한 번에 자동 생성되었습니다!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 실패 (Supabase 설정을 확인하세요): {e}")
                else:
                    st.warning("고객 ID와 업체명은 필수입니다.")

    # ==========================================
    # 4-B. [고객 모드] 업체 대표님 전용
    # ==========================================
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
                st.subheader("💡 공민준 센터장의 맞춤형 경영 전략")
                st.info(user_data['strategy_comment'])
            else:
                st.warning("발행된 리포트가 없습니다.")
        except:
             st.warning("데이터베이스 연동 중입니다.")
