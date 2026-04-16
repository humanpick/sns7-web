import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt
import altair as alt

# ==========================================
# 1. 프리미엄 UI 디자인 및 시스템 설정 (CSS)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# 네이비 & 골드 테마 색상 정의
NAVY = "#001F3F"
GOLD = "#D4AF37"

# 💡 [해결] f-string 외부에서 스타일을 정의하여 상단 텍스트 노출 에러를 원천 차단합니다.
style_code = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;500;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Noto Sans KR', sans-serif !important; 
    }}
    
    .stApp {{ background-color: #FDFDFD !important; }}
    
    /* 사이드바 디자인 */
    [data-testid="stSidebar"] {{ 
        background-color: {NAVY} !important; 
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div > div {{
        color: white !important;
    }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 버튼 디자인 */
    .stButton>button {{
        background-color: {GOLD} !important;
        color: {NAVY} !important;
        border-radius: 5px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }}

    /* 레이아웃 최적화 */
    .block-container {{ 
        padding-top: 1rem !important; 
        margin-top: -30px !important; 
    }}
    header {{ visibility: hidden !important; height: 0px !important; }}
    [data-testid="stElementActions"], .vega-actions {{ display: none !important; }}
    
    /* 카드형 메트릭 디자인 */
    div[data-testid="metric-container"] {{
        background-color: white !important;
        border: 1px solid #E0E0E0 !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05) !important;
    }}
</style>
<meta name="google" content="notranslate">
"""
st.markdown(style_code, unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 정보 (민준님의 Key를 입력하세요!)
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
# 2. 사용자 인증 및 데이터 로딩
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

credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)

authenticator.login('main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    
    try:
        user_res = supabase.table('users').select('name').eq('username', username).execute()
        real_name = user_res.data[0]['name'] if user_res.data else credentials['usernames'][username]['name']
    except: real_name = credentials['usernames'][username]['name']

    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}** 대표님 반갑습니다.")
        authenticator.logout('시스템 로그아웃', 'sidebar')

    if credentials['usernames'][username]['role'] == 'admin':
        st.title("👑 관리자 대시보드")
        st.info("관리자 권한으로 접속 중입니다.")
    else:
        # ==========================================
        # 3. 맞춤형 경영 리포트 출력
        # ==========================================
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df.get('created_at', pd.Timestamp.now())).dt.tz_localize(None)
                df['날짜'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                df['점수'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)
                df['매출_억'] = df['매출'] / 10000.0  # 💡 엔진 에러 방지용 스케일링

                df['점수_텍스트'] = df['점수'].astype(str)
                df['매출_텍스트'] = df['매출'].apply(lambda x: f"{x:,}")

                latest = df.iloc[-1]
                safe_score, safe_sales = int(latest['점수']), int(latest['매출'])
                
                # 상단 헤더 배너
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {NAVY} 0%, #003366 100%); 
                                padding: 30px; border-radius: 15px; border-left: 10px solid {GOLD}; 
                                color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <h1 style="color: {GOLD}; margin-bottom: 10px; font-weight: 700;">📈 {real_name} 대표님 맞춤형 경영 리포트</h1>
                        <p style="font-size: 18px; margin: 0; opacity: 0.9;">현재 경영 상태: 
                            <span style="font-weight: 700; color: {'#58D68D' if safe_score > 839 else '#F1948A'};">
                                {"정책자금 승인 권장권" if safe_score > 839 else "신용 및 매출 관리 집중 기간"}
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                m1.metric("성함", real_name)
                m2.metric("최신 신용점수", f"{safe_score} 점")
                m3.metric("최신 월 매출액", f"{safe_sales:,} 만원")

                st.divider()

                col1, col2 = st.columns(2)
                x_ax = alt.X('날짜:N', title='분석 기준일', axis=alt.Axis(labelAngle=0, labelColor='black'))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999], zero=False, clamp=True), title='신용점수')
                    )
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    
                    chart1 = alt.layer(
                        rule, 
                        base.mark_line(color='#ff4b4b', size=3), 
                        base.mark_circle(size=150, color='#ff4b4b'), 
                        base.mark_text(dy=-20, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='점수_텍스트:N')
                    ).properties(height=350)
                    
                    st.altair_chart(chart1, use_container_width=True, theme=None)
                    st.caption("※ 회색 점선: 정책자금 권장 기준선 (839점)")

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    base_s = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2], clamp=True), title='매출액 (단위: 억원)',
                                axis=alt.Axis(values=[0, 0.5, 1.0, 1.5, 2.0], format=".1f", labelColor='black'))
                    )
                    
                    chart2 = alt.layer(
                        base_s.mark_line(color='#0068c9', size=3), 
                        base_s.mark_circle(size=150, color='#0068c9'),
                        base_s.mark_text(dy=-20, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='매출_텍스트:N')
                    ).properties(height=350)
                    
                    st.altair_chart(chart2, use_container_width=True, theme=None)
                    st.caption("※ 차트 범위: 0원 ~ 2억 원")

                st.divider()
                st.subheader("💡 공민준 센터장의 경영 전략 제언")
                st.info(latest.get('strategy_comment', "전문 분석 결과가 수립 중입니다. 잠시만 기다려 주세요."))
                
            else:
                st.warning("등록된 데이터가 없습니다. 관리자에게 문의하세요.")
        except Exception as e:
             st.error(f"화면 구성 중 오류 발생: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error('아이디 또는 비밀번호를 다시 확인해 주세요.')
elif st.session_state.get("authentication_status") is None:
    st.info('발급받으신 CEO 계정 정보를 입력하여 로그인해 주세요.')
