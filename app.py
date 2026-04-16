import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# [필수] 센터장님의 Supabase 정보를 입력하세요. (따옴표 유지)
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
# 2. 데이터베이스 통신 함수 (유저 및 고객 정보)
# ==========================================
def fetch_users():
    """DB의 users 테이블에서 로그인 정보를 가져옵니다."""
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'name': user['name'],
                'password': user['password'], # 해시화된 암호
                'role': user['role']
            }
        return credentials
    except Exception as e:
        return {'usernames': {}}

def update_password_in_db(username, hashed_password):
    """변경된 비밀번호를 DB에 영구 저장합니다."""
    supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()

# ==========================================
# 3. 로그인 및 인증 시스템 (최신 버전 문법)
# ==========================================
# DB에서 실시간으로 유저 명부 로드
credentials = fetch_users()

# 인증 객체 초기화
authenticator = stauth.Authenticate(
    credentials,
    'ceo_portal_cookie', 
    'signature_key',     
    cookie_expiry_days=30 
)

# 로그인 화면 렌더링 (최신 버전은 반환값 대신 세션을 확인합니다)
authenticator.login('main')

# 세션 상태에 따른 로직 분기
if st.session_state["authentication_status"] == False:
    st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
elif st.session_state["authentication_status"] == None:
    st.info('발급받으신 아이디와 비밀번호를 입력해 주세요.')
    
elif st.session_state["authentication_status"] == True:
    
    # 세션에서 현재 로그인한 유저 정보 추출
    username = st.session_state["username"]
    name = st.session_state["name"]
    user_role = credentials['usernames'][username]['role']
    
    # --- 좌측 사이드바 (메뉴 및 설정) ---
    with st.sidebar:
        st.write(f"**{name}**님 반갑습니다.")
        st.divider()
        
        # 비밀번호 변경 기능 (최신 버전 호환)
        try:
            if authenticator.reset_password(username, 'sidebar'):
                # 변경된 해시값을 DB에 업데이트
                new_hashed_pw = credentials['usernames'][username]['password']
                update_password_in_db(username, new_hashed_pw)
                st.success('비밀번호가 안전하게 변경되었습니다.')
        except Exception as e:
            st.error(f"비밀번호 변경 중 오류: {e}")
            
        st.divider()
        authenticator.logout('로그아웃', 'sidebar')

    # ==========================================
    # 4-A. [관리자 모드] 공민준 센터장 전용 화면
    # ==========================================
    if user_role == 'admin':
        st.title("👑 CEO 포털 통합 관리자 대시보드")
        st.caption("고객 데이터를 관리하고 맞춤형 전략 리포트를 발행합니다.")
        
        # 전체 데이터 조회 시도
        try:
            res = supabase.table('client_data').select('*').execute()
            if res.data:
                all_df = pd.DataFrame(res.data)
                st.subheader("📊 현재 등록된 고객 리스트")
                st.dataframe(all_df, use_container_width=True, hide_index=True)
            else:
                st.info("아직 등록된 고객 데이터가 없습니다.")
        except:
            st.warning("⚠️ 'client_data' 테이블을 생성해야 데이터를 불러올 수 있습니다.")
        
        st.divider()
        st.subheader("➕ 신규 경영 리포트 발행")
        with st.form("new_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_id = st.text_input("고객 ID (접속용 ID)", placeholder="예: client_kim")
                c_name = st.text_input("업체명", placeholder="예: (주)인슈테크")
            with col2:
                c_score = st.number_input("신용점수", min_value=0, max_value=1000, value=850)
                c_sales = st.number_input("월 매출 (만원 단위)", min_value=0, step=100)
            c_comment = st.text_area("센터장님 전용 전략 코멘트 (해당 고객에게만 노출됩니다)")
            
            if st.form_submit_button("리포트 DB 저장 및 발행"):
                if c_id and c_name:
                    try:
                        supabase.table('client_data').insert({
                            'client_id': c_id, 
                            'company_name': c_name,
                            'credit_score': c_score, 
                            'monthly_sales': c_sales,
                            'strategy_comment': c_comment
                        }).execute()
                        st.success(f"[{c_name}] 리포트가 성공적으로 저장되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"데이터 저장 실패 (테이블 확인 필요): {e}")
                else:
                    st.warning("고객 ID와 업체명은 필수 입력 사항입니다.")

    # ==========================================
    # 4-B. [고객 모드] 업체 대표님 전용 화면
    # ==========================================
    else:
        st.title(f"📈 {name} 대표님 맞춤형 경영 대시보드")
        
        try:
            # 본인 데이터만 콕 집어서 필터링 (데이터 격리)
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            
            if res.data:
                user_data = res.data[0] 
                
                # 시각화 지표 카드
                col1, col2, col3 = st.columns(3)
                col1.metric("업체명", user_data['company_name'])
                col2.metric("현재 신용점수", f"{user_data['credit_score']} 점")
                col3.metric("최근 월 매출", f"{user_data['monthly_sales']:,} 만원")
                
                st.divider()
                st.subheader("💡 공민준 센터장의 맞춤형 경영 전략")
                st.info(user_data['strategy_comment'])
                
                st.caption("※ 본 리포트는 민준 센터장의 전문 진단 결과이며, 본인 외에는 열람이 불가능합니다.")
            else:
                st.warning("아직 발행된 경영 리포트가 없습니다. 담당 센터장에게 문의해 주세요.")
        except:
             st.warning("경영 데이터를 불러오는 중입니다. 잠시만 기다려 주세요.")
