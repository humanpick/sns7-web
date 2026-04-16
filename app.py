import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt  # 💡 Hasher 에러를 잡기 위해 엔진을 직접 호출합니다.

# ==========================================
# 1. 프리미엄 UI 디자인 및 시스템 설정
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"

style_code = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;500;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Noto Sans KR', sans-serif !important; }}
    .stApp {{ background-color: #FDFDFD !important; }}
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border-radius: 5px !important; font-weight: 700 !important; border: none !important;
        padding: 0.5rem 1rem !important;
    }}
    .block-container {{ padding-top: 1rem !important; margin-top: -30px !important; }}
    header {{ visibility: hidden !important; height: 0px !important; }}
    [data-testid="stElementActions"], .vega-actions {{ display: none !important; }}
    div[data-testid="metric-container"] {{
        background-color: white !important; border: 1px solid #E0E0E0 !important;
        padding: 15px !important; border-radius: 10px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05) !important;
    }}
</style>
<meta name="google" content="notranslate">
"""
st.markdown(style_code, unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 정보
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource(show_spinner=False)
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"DB 연결 실패: {e}")
    st.stop()

# ==========================================
# 2. 데이터베이스 및 인증 구조 (철벽 방어)
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        # 💡 [구조 고정] 반드시 'usernames' 키를 가진 딕셔너리로 만듭니다.
        creds = {'usernames': {}}
        if response.data:
            for user in response.data:
                u_id = str(user['username'])
                creds['usernames'][u_id] = {
                    'name': str(user['name']),
                    'password': str(user['password']),
                    'role': str(user.get('role', 'viewer')),
                    'phone': str(user.get('phone', ''))
                }
        return creds
    except:
        return {'usernames': {}}

credentials = fetch_users()

# 인증기 초기화 (가장 보수적이고 안전한 설정)
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name='ceo_portal_cookie',
    key='signature_key',
    cookie_expiry_days=30
)

# 로그인 화면
authenticator.login('main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    all_users = credentials.get('usernames', {})
    user_data = all_users.get(username, {})
    
    user_role = user_data.get('role', 'viewer')
    real_name = user_data.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # ------------------------------------------
    # 👑 [ADMIN] 관리자 대시보드
    # ------------------------------------------
    if user_role == 'admin':
        st.title("👑 관리자 데이터 센터")
        tab1, tab2, tab3 = st.tabs(["📝 데이터 입력", "👥 고객 등록 및 관리", "📜 전체 리포트 이력"])
        
        # [Tab 1: 데이터 입력]
        with tab1:
            st.subheader("리포트 수치 입력")
            viewer_list = [u for u in all_users if all_users[u].get('role') != 'admin']
            if not viewer_list:
                st.info("고객을 먼저 등록해 주세요.")
            else:
                selected_client = st.selectbox("대상을 선택하세요", viewer_list, 
                                               format_func=lambda x: f"{all_users[x].get('name')} ({x})")
                with st.form("data_input_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_score = st.number_input("신용점수 (500~999)", min_value=500, max_value=999, value=850)
                    with col2:
                        new_sales = st.number_input("월 매출액 (만원)", min_value=0, value=1500)
                    new_strategy = st.text_area("공민준 센터장의 전략 제언")
                    if st.form_submit_button("데이터 저장"):
                        supabase.table('client_data').insert({
                            "client_id": selected_client, "credit_score": new_score, 
                            "monthly_sales": new_sales, "strategy_comment": new_strategy
                        }).execute()
                        st.success("저장되었습니다!")
                        st.rerun()

        # [Tab 2: 고객 등록 및 관리]
        with tab2:
            st.subheader("신규 고객 계정 생성")
            with st.form("user_reg_form"):
                reg_id = st.text_input("1. ID (로그인용)")
                reg_pw = st.text_input("2. 비밀번호 설정", type="password")
                reg_name = st.text_input("3. 고객 성함")
                reg_phone = st.text_input("4. 휴대폰 번호 (숫자만)")
                
                if st.form_submit_button("고객 정보 저장 및 등록"):
                    if not reg_id or not reg_pw or not reg_name:
                        st.warning("ID, 비번, 성함은 필수입니다.")
                    elif reg_id in all_users:
                        st.error("이미 존재하는 ID입니다.")
                    else:
                        try:
                            # 💡 [에러 박멸] 라이브러리 함수 대신 bcrypt를 직접 사용하여 암호화합니다.
                            # 이 방식은 '리스트 인덱스' 에러가 절대 발생할 수 없습니다.
                            hashed_pw = bcrypt.hashpw(reg_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            
                            supabase.table('users').insert({
                                "username": reg_id, "name": reg_name, 
                                "password": hashed_pw, "role": "viewer", "phone": reg_phone
                            }).execute()
                            st.success(f"✅ {reg_name} 대표님 등록 완료!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"등록 실패: {e}")
            
            st.divider()
            st.subheader("현재 등록된 고객 리스트")
            cl_display = [{"ID": k, "이름": v.get('name'), "번호": v.get('phone')} 
                          for k, v in all_users.items() if v.get('role') != 'admin']
            if cl_display: st.table(pd.DataFrame(cl_display))

        # [Tab 3: 전체 리포트 이력]
        with tab3:
            st.subheader("전체 발행 기록")
            all_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if all_res.data:
                all_df = pd.DataFrame(all_res.data)
                all_df['고객명'] = all_df['client_id'].apply(lambda x: all_users.get(x, {}).get('name', x))
                st.dataframe(all_df[['created_at', '고객명', 'credit_score', 'monthly_sales']], use_container_width=True)

    # ------------------------------------------
    # 📈 [VIEWER] 고객 리포트 화면
    # ------------------------------------------
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df['날짜'] = df['created_at'].dt.strftime('%Y-%m-%d')
                df['점수'] = pd.to_numeric(df['credit_score']).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales']).astype(int)
                df['매출_억'] = df['매출'] / 10000.0

                latest = df.iloc[-1]
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {NAVY} 0%, #003366 100%); 
                                padding: 30px; border-radius: 15px; border-left: 10px solid {GOLD}; 
                                color: white; text-align: center; margin-bottom: 25px;">
                        <h1 style="color: {GOLD}; margin-bottom: 10px;">📈 {real_name} 대표님 리포트</h1>
                        <p style="font-size: 18px; margin: 0;">현재 경영 상태: 
                            <span style="font-weight: 700; color: {'#58D68D' if int(latest['점수']) > 839 else '#F1948A'};">
                                {"정책자금 승인 권장" if int(latest['점수']) > 839 else "신용 관리 필요"}
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                m1.metric("성함", real_name)
                m2.metric("최신 신용점수", f"{int(latest['점수'])} 점")
                m3.metric("최신 월 매출액", f"{int(latest['매출']):,} 만원")

                st.divider()
                col1, col2 = st.columns(2)
                x_ax = alt.X('날짜:N', title='분석일')
                with col1:
                    base = alt.Chart(df).encode(x=x_ax, y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999])))
                    st.altair_chart(base.mark_line(color='red', size=3) + base.mark_circle(size=100, color='red'), use_container_width=True, theme=None)
                with col2:
                    base_s = alt.Chart(df).encode(x=x_ax, y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2])))
                    st.altair_chart(base_s.mark_line(color='blue', size=3) + base_s.mark_circle(size=100, color='blue'), use_container_width=True, theme=None)
                
                st.info(latest['strategy_comment'])
            else:
                st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e:
             st.error(f"데이터 로딩 오류: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error('정보를 다시 확인해 주세요.')
elif st.session_state.get("authentication_status") is None:
    st.info('로그인 후 이용 가능합니다.')
