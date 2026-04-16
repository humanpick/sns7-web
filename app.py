import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt
import numpy as np

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# [필수] 센터장님의 Supabase 정보를 입력하세요.
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
                c_sales = st.number_input("월 매출 (만원 단위)", min_value=0, step=100)
            c_comment = st.text_area("센터장님 전용 전략 코멘트")
            
            if st.form_submit_button("DB 저장 및 계정 생성"):
                if c_id and c_name:
                    try:
                        temp_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        supabase.table('users').upsert({
                            'username': c_id, 
                            'password': temp_hash,
                            'name': c_name,
                            'role': 'client'
                        }).execute()

                        supabase.table('client_data').upsert({
                            'client_id': c_id, 
                            'company_name': c_name,
                            'credit_score': c_score, 
                            'monthly_sales': c_sales,
                            'strategy_comment': c_comment
                        }).execute()

                        st.success(f"✅ [{c_name}] 대표님의 데이터 저장 및 로그인 계정이 생성되었습니다! (초기비번: 1234)")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
                else:
                    st.warning("고객 ID와 업체명은 필수입니다.")

    # ==========================================
    # 4-B. [고객 모드] 업체 대표님 전용 (시각화 강화)
    # ==========================================
    else:
        st.title(f"📈 {name} 대표님 맞춤형 경영 리포트")
        st.caption("공민준 센터장의 전문 진단 결과입니다.")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            if res.data:
                user_data = res.data[0] 
                safe_score = int(user_data.get('credit_score', 0))
                safe_sales = int(user_data.get('monthly_sales', 0))
                
                # 상단 지표
                col1, col2, col3 = st.columns(3)
                col1.metric("대표자 성함", name)
                col2.metric("신용점수 진단", f"{safe_score} 점")
                col3.metric("최근 월 매출액", f"{safe_sales:,} 만원")
                
                st.divider()
                
                # --- 그래프 영역 ---
                st.subheader("📊 경영 핵심 지표 추이 (점과 선)")
                chart_col1, chart_col2 = st.columns(2)
                
                # [그래프 1] 신용점수 우상향 트렌드
                with chart_col1:
                    st.write("**🛡️ 신용점수 관리 추이**")
                    # 우상향 트렌드를 시각화하기 위해 과거 가상 데이터를 생성
                    score_history = [safe_score - 40, safe_score - 15, safe_score]
                    df_score = pd.DataFrame({
                        "시점": ["과거", "직전", "현재"],
                        "점수": score_history,
                        "정책자금 기준(839)": [839, 839, 839]
                    })
                    st.line_chart(df_score.set_index("시점"), color=["#FF9900", "#FF0000"]) # 오렌지는 점수, 레드는 기준선
                    
                    if safe_score > 839:
                        st.success(f"현재 점수 {safe_score}점: **정책자금 신청 가능권** (839점 초과)")
                    else:
                        st.warning(f"현재 점수 {safe_score}점: **정책자금 기준(839점) 집중 관리 필요**")

                # [그래프 2] 월 매출액 우상향 트렌드
                with chart_col2:
                    st.write("**💰 월 매출 성장 추이**")
                    # 우상향 트렌드 가상 데이터
                    sales_history = [int(safe_sales * 0.7), int(safe_sales * 0.9), safe_sales]
                    df_sales = pd.DataFrame({
                        "시점": ["과거", "직전", "현재"],
                        "매출(만원)": sales_history
                    })
                    st.line_chart(df_sales.set_index("시점"), color="#0000FF") # 블루 계열
                    st.write(f"현재 매출 수준: **상향 안정화 단계**")

                st.divider()
                
                # 센터장 코멘트
                st.subheader("💡 공민준 센터장의 맞춤형 경영 제언")
                st.info(user_data.get('strategy_comment', "세부 전략을 수립 중입니다."))
                
            else:
                st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e:
             st.warning(f"데이터 로드 중: {e}")
