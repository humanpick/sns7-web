import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt
import altair as alt

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
# 2. 데이터베이스 통신 함수
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'email': f"{user['username']}@ceo.com", 
                'name': user['name'], 'password': user['password'], 'role': user['role']
            }
        return credentials
    except: return {'usernames': {}}

# ==========================================
# 3. 사용자 인증 시스템
# ==========================================
credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    user_role = credentials['usernames'][username]['role']
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{credentials['usernames'][username]['name']}**님 환영합니다.")
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
            user_list = [u for u in credentials['usernames'] if credentials['usernames'][u]['role'] != 'admin']
            if not user_list:
                st.info("먼저 고객을 등록해 주세요.")
            else:
                selected_client = st.selectbox("고객을 선택하세요", user_list, 
                                               format_func=lambda x: f"{credentials['usernames'][x]['name']} ({x})")
                
                with st.form("data_input_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_score = st.number_input("신용점수 (500~999)", min_value=500, max_value=999, value=850)
                    with col2:
                        new_sales = st.number_input("월 매출액 (단위: 만원)", min_value=0, value=1500)
                    new_strategy = st.text_area("공민준 센터장의 경영 제언")
                    
                    if st.form_submit_button("데이터 저장"):
                        data = {"client_id": selected_client, "credit_score": new_score, 
                                "monthly_sales": new_sales, "strategy_comment": new_strategy}
                        supabase.table('client_data').insert(data).execute()
                        st.success("데이터가 성공적으로 저장되었습니다!")
                        st.rerun()

        # [Tab 2: 고객 등록 및 관리]
        with tab2:
            st.subheader("신규 고객 계정 생성")
            # 💡 [업데이트] 요청하신 대로 입력 순서를 변경하고 ID 자동 생성 로직을 넣었습니다.
            with st.form("user_reg_form"):
                new_name = st.text_input("1. 고객 성함")
                new_pw = st.text_input("2. 비밀번호 설정", type="password")
                new_phone = st.text_input("3. 휴대폰 번호 (숫자만 입력, 예: 01012345678)")
                
                st.caption("※ ID는 'kdj + 휴대폰 뒷자리 4자리'로 자동 생성됩니다.")
                
                if st.form_submit_button("고객 등록 및 ID 생성"):
                    if not new_name or not new_pw or len(new_phone) < 4:
                        st.warning("모든 정보를 정확히 입력해 주세요. (휴대폰 번호 4자리 이상 필수)")
                    else:
                        # 💡 ID 자동 생성 로직
                        generated_id = f"kdj{new_phone[-4:]}"
                        
                        # 비밀번호 암호화
                        hashed_pw = stauth.Hasher([new_pw]).generate()[0]
                        
                        new_user = {
                            "username": generated_id, 
                            "name": new_name, 
                            "password": hashed_pw, 
                            "role": "viewer"
                        }
                        
                        try:
                            supabase.table('users').insert(new_user).execute()
                            st.success(f"✅ {new_name} 대표님 등록 완료! (아이디: {generated_id})")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"등록 실패 (ID 중복 가능성): {e}")
            
            st.divider()
            st.subheader("현재 등록된 고객 리스트")
            client_data_list = [{"ID": k, "이름": v['name']} for k, v in credentials['usernames'].items() if v['role'] != 'admin']
            if client_data_list:
                st.table(pd.DataFrame(client_data_list))

        # [Tab 3: 전체 리포트 이력]
        with tab3:
            st.subheader("전체 발행 리포트 기록")
            all_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if all_res.data:
                all_df = pd.DataFrame(all_res.data)
                all_df['고객명'] = all_df['client_id'].apply(lambda x: credentials['usernames'].get(x, {}).get('name', x))
                st.dataframe(all_df[['created_at', '고객명', 'credit_score', 'monthly_sales', 'strategy_comment']], use_container_width=True)
            else:
                st.write("발행된 리포트가 없습니다.")

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
                df['점수_텍스트'] = df['점수'].astype(str)
                df['매출_텍스트'] = df['매출'].apply(lambda x: f"{x:,}")

                latest = df.iloc[-1]
                
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {NAVY} 0%, #003366 100%); 
                                padding: 30px; border-radius: 15px; border-left: 10px solid {GOLD}; 
                                color: white; text-align: center; margin-bottom: 25px;">
                        <h1 style="color: {GOLD}; margin-bottom: 10px;">📈 {credentials['usernames'][username]['name']} 대표님 경영 리포트</h1>
                        <p style="font-size: 18px; margin: 0;">현재 경영 상태: 
                            <span style="font-weight: 700; color: {'#58D68D' if int(latest['점수']) > 839 else '#F1948A'};">
                                {"정책자금 승인 권장권" if int(latest['점수']) > 839 else "신용 관리 집중 기간"}
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                m1.metric("성함", credentials[username]['name'])
                m2.metric("최신 신용점수", f"{int(latest['점수'])} 점")
                m3.metric("최신 월 매출액", f"{int(latest['매출']):,} 만원")

                st.divider()

                col1, col2 = st.columns(2)
                x_ax = alt.X('날짜:N', title='분석 기준일', axis=alt.Axis(labelAngle=0))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base = alt.Chart(df).encode(x=x_ax, y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999], zero=False)))
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    chart1 = alt.layer(rule, base.mark_line(color='#ff4b4b', size=3), base.mark_circle(size=150, color='#ff4b4b'),
                                       base.mark_text(dy=-20, fontSize=15, fontWeight='bold').encode(text='점수_텍스트:N')).properties(height=350)
                    st.altair_chart(chart1, use_container_width=True, theme=None)

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    base_s = alt.Chart(df).encode(x=x_ax, y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), 
                                                                  axis=alt.Axis(values=[0, 0.5, 1.0, 1.5, 2.0], format=".1f")))
                    chart2 = alt.layer(base_s.mark_line(color='#0068c9', size=3), base_s.mark_circle(size=150, color='#0068c9'),
                                       base_s.mark_text(dy=-20, fontSize=15, fontWeight='bold').encode(text='매출_텍스트:N')).properties(height=350)
                    st.altair_chart(chart2, use_container_width=True, theme=None)

                st.divider()
                st.subheader("💡 공민준 센터장의 경영 전략 제언")
                st.info(latest['strategy_comment'])
            else:
                st.warning("발행된 리포트가 없습니다.")
        except Exception as e:
             st.error(f"데이터 로딩 오류: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error('아이디 또는 비밀번호를 다시 확인해 주세요.')
elif st.session_state.get("authentication_status") is None:
    st.info('제공받으신 CEO 계정 정보를 입력하여 로그인해 주세요.')
