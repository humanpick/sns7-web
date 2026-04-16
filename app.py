import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 시스템 설정 및 독자적 가독성 디자인 (CSS)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_GRAY = "#F8F9FA"

# 가독성을 극대화한 커스텀 스타일
st.markdown(f"""
    <meta name="google" content="notranslate">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_GRAY};
    }}
    
    /* 메인 컨테이너 여백 조정 */
    .block-container {{ padding: 2rem 5rem !important; }}
    
    /* 사이드바 디자인 */
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 카드형 디자인 */
    .report-card {{
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }}
    
    /* 메트릭 폰트 강조 */
    .metric-label {{ font-size: 1rem; color: #666; margin-bottom: 0.5rem; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 700; color: {NAVY}; }}

    /* 버튼 스타일 */
    .stButton>button {{
        background-color: {GOLD} !important;
        color: {NAVY} !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
    }}
    
    /* 헤더 감추기 */
    header {{ visibility: hidden !important; }}
    </style>
""", unsafe_allow_html=True)

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
# 2. 데이터 및 인증 로직 (V9 무결성 유지)
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        creds = {'usernames': {}}
        if response.data:
            for user in response.data:
                u_id = str(user['username'])
                creds['usernames'][u_id] = {
                    'name': str(user['name']),
                    'password': str(user['password']),
                    'role': str(user.get('role', 'viewer'))
                }
        return creds
    except: return {'usernames': {}}

credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    user_data = credentials.get('usernames', {}).get(username, {})
    user_role = user_data.get('role', 'viewer')
    real_name = user_data.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('로그아웃', 'sidebar')

    # ------------------------------------------
    # 👑 [ADMIN] 관리자 대시보드
    # ------------------------------------------
    if user_role == 'admin':
        st.title("👑 관리자 데이터 센터")
        tab1, tab2, tab3 = st.tabs(["📝 데이터 입력", "👥 고객 등록", "📜 전체 이력"])
        
        with tab1:
            viewer_list = [u for u in credentials['usernames'] if credentials['usernames'][u].get('role') != 'admin']
            if not viewer_list: st.info("고객을 등록해 주세요.")
            else:
                selected_client = st.selectbox("고객 선택", viewer_list, format_func=lambda x: f"{credentials['usernames'][x].get('name')} ({x})")
                with st.form("input_form", clear_on_submit=True):
                    comp_name = st.text_input("업체명")
                    c1, c2 = st.columns(2)
                    score = c1.number_input("신용점수", 500, 999, 850)
                    sales = c2.number_input("월 매출(만원)", 0, 100000, 1500)
                    comment = st.text_area("센터장 제언")
                    if st.form_submit_button("리포트 발행"):
                        supabase.table('client_data').insert({
                            "client_id": selected_client, "company_name": comp_name,
                            "credit_score": str(score), "monthly_sales": str(sales), "strategy_comment": comment
                        }).execute()
                        st.success("발행 완료")
                        st.rerun()

        with tab2:
            with st.form("reg_form"):
                r_id = st.text_input("아이디")
                r_pw = st.text_input("비번", type="password")
                r_name = st.text_input("이름")
                if st.form_submit_button("고객 계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.success("생성 완료")
                    st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 가독성 중심 고객 리포트
    # ------------------------------------------
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%m-%d')
                df['점수'] = pd.to_numeric(df['credit_score']).astype(int)
                df['매출_억'] = pd.to_numeric(df['monthly_sales']).astype(int) / 10000.0
                latest = df.iloc[-1]

                # 1. 슬림하고 우아한 헤더
                st.markdown(f"""
                    <div style="border-bottom: 2px solid {GOLD}; padding-bottom: 10px; margin-bottom: 30px;">
                        <span style="color: {NAVY}; font-size: 1.2rem; font-weight: 300;">SNS7 PREMIUM REPORT</span>
                        <h1 style="color: {NAVY}; margin-top: 5px;">{real_name} 대표님 맞춤형 경영 리포트</h1>
                    </div>
                """, unsafe_allow_html=True)

                # 2. 핵심 지표 요약 (심플 카드)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f'<div class="report-card"><p class="metric-label">업체명</p><p class="metric-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="report-card"><p class="metric-label">현재 신용점수</p><p class="metric-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="report-card"><p class="metric-label">월 매출액</p><p class="metric-value">{int(pd.to_numeric(latest["monthly_sales"])):,} 만원</p></div>', unsafe_allow_html=True)

                # 3. 그래프 섹션 (여백 확보)
                st.write("")
                g_col1, g_col2 = st.columns(2)
                
                with g_col1:
                    st.markdown('<p style="font-weight:700; color:#333;">🛡️ 신용점수 추이</p>', unsafe_allow_html=True)
                    chart1 = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=4, interpolate='monotone').encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 1000]), title=None)
                    ).properties(height=300)
                    st.altair_chart(chart1 + chart1.mark_circle(size=100, color='#E74C3C'), use_container_width=True)

                with g_col2:
                    st.markdown('<p style="font-weight:700; color:#333;">💰 매출 성장 추이 (단위: 억)</p>', unsafe_allow_html=True)
                    chart2 = alt.Chart(df).mark_area(
                        line={'color': '#3498DB'},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None)
                    ).properties(height=300)
                    st.altair_chart(chart2, use_container_width=True)

                # 4. 센터장 전략 제언 (골드 포인트)
                st.markdown(f"""
                    <div style="background-color: {NAVY}; color: white; padding: 2.5rem; border-radius: 15px; margin-top: 2rem;">
                        <h3 style="color: {GOLD}; margin-bottom: 1rem;">💡 공민준 센터장의 핵심 경영 제언</h3>
                        <p style="font-size: 1.1rem; line-height: 1.8; opacity: 0.9;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 5. 하단 고정 프로필 및 명언
                st.write("---")
                f1, f2 = st.columns([1, 1])
                with f1:
                    st.markdown(f"""
                        <div style="font-size: 0.9rem; color: #666;">
                            <b>공민준 지점장</b><br>
                            연락처: 010-XXXX-XXXX<br>
                            SNS7 비즈니스 센터
                        </div>
                    """, unsafe_allow_html=True)
                with f2:
                    st.markdown("""
                        <div style="text-align: right; font-style: italic; color: #999; font-size: 0.9rem;">
                            "성공은 결코 우연이 아니다. 그것은 고된 작업, 인내, 배움, 그리고 희생의 결과다."
                        </div>
                    """, unsafe_allow_html=True)

            else: st.warning("발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보 오류')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력해 주세요.')
