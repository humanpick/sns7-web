import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 시스템 설정 및 완벽한 가독성 디자인 (CSS)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_GRAY = "#F8F9FA"

# 💡 [핵심 해결] 모든 중괄호를 {{ }}로 이중 처리하여 상단 텍스트 노출을 완벽 차단했습니다.
st.markdown(f"""
    <meta name="google" content="notranslate">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_GRAY} !important;
    }}
    
    /* 상단 여백 및 헤더 제거 */
    header {{ visibility: hidden !important; height: 0px !important; }}
    .block-container {{ padding: 2rem 5rem !important; margin-top: -30px !important; }}
    
    /* 사이드바 디자인 */
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 카드 및 메트릭 디자인 */
    .report-card {{
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }}
    
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
    
    /* 로그인 박스 테두리 노출 방지 */
    [data-testid="stMarkdownContainer"] p {{ margin-bottom: 0px; }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 정보 (민준 님의 정보를 유지하세요)
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
# 2. 데이터베이스 및 인증 로직
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        creds = {'usernames': {}}
        if response.data:
            for user in response.data:
                u_id = str(user['username'])
                creds['usernames'][u_id] = {{
                    'name': str(user['name']),
                    'password': str(user['password']),
                    'role': str(user.get('role', 'viewer'))
                }}
        return creds
    except: return {'usernames': {}}

credentials = fetch_users()
# 세션 쿠키 이름과 서명 키를 명확히 고정합니다.
authenticator = stauth.Authenticate(credentials, 'sns7_ceo_portal', 'auth_key_2026', cookie_expiry_days=30)

# 로그인 화면 출력
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
        tab1, tab2, tab3 = st.tabs(["📝 리포트 발행", "👥 고객 계정 관리", "📜 발행 이력"])
        
        with tab1:
            viewer_list = [u for u in all_users if all_users[u].get('role') != 'admin']
            if not viewer_list: st.info("등록된 고객이 없습니다.")
            else:
                selected_client = st.selectbox("리포트 대상 선택", viewer_list, format_func=lambda x: f"{all_users[x].get('name')} ({x})")
                with st.form("input_form", clear_on_submit=True):
                    comp_name = st.text_input("업체명 (예: 불타는닭발)")
                    c1, c2 = st.columns(2)
                    score = c1.number_input("신용점수", 500, 999, 850)
                    sales = c2.number_input("월 매출액 (만원)", 0, 100000, 1500)
                    comment = st.text_area("공민준 센터장의 경영 전략 제언")
                    if st.form_submit_button("리포트 전송"):
                        supabase.table('client_data').insert({
                            "client_id": selected_client, "company_name": comp_name,
                            "credit_score": str(score), "monthly_sales": str(sales), "strategy_comment": comment
                        }).execute()
                        st.success("리포트가 성공적으로 전송되었습니다.")
                        st.rerun()

        with tab2:
            st.subheader("신규 고객 등록")
            with st.form("reg_form"):
                r_id = st.text_input("희망 아이디")
                r_pw = st.text_input("비밀번호 설정", type="password")
                r_name = st.text_input("고객 성함")
                if st.form_submit_button("계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.success(f"{r_name} 고객님이 등록되었습니다.")
                    st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 프리미엄 경영 리포트
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

                # 1. 심플 프리미엄 헤더
                st.markdown(f"""
                    <div style="border-bottom: 2px solid {GOLD}; padding-bottom: 10px; margin-bottom: 30px;">
                        <span style="color: {NAVY}; font-size: 1.1rem; font-weight: 300; letter-spacing: 2px;">SNS7 BUSINESS ANALYTICS</span>
                        <h1 style="color: {NAVY}; margin-top: 5px; font-weight: 700;">{real_name} 대표님 맞춤형 경영 리포트</h1>
                    </div>
                """, unsafe_allow_html=True)

                # 2. 핵심 지표 섹션
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f'<div class="report-card"><p class="metric-label">분석 업체명</p><p class="metric-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="report-card"><p class="metric-label">현재 신용점수</p><p class="metric-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="report-card"><p class="metric-label">최근 월 매출</p><p class="metric-value">{int(pd.to_numeric(latest["monthly_sales"])):,} 만원</p></div>', unsafe_allow_html=True)

                # 3. 데이터 시각화
                st.write("")
                g_col1, g_col2 = st.columns(2)
                
                with g_col1:
                    st.markdown('<p style="font-weight:700; color:#444; margin-bottom:15px;">🛡️ 신용 분석 추이</p>', unsafe_allow_html=True)
                    line = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=4, interpolate='monotone').encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 1000]), title=None)
                    )
                    points = line.mark_circle(size=120, color='#E74C3C')
                    st.altair_chart((line + points).properties(height=300), use_container_width=True)

                with g_col2:
                    st.markdown('<p style="font-weight:700; color:#444; margin-bottom:15px;">💰 매출 성장 곡선 (억 단위)</p>', unsafe_allow_html=True)
                    area = alt.Chart(df).mark_area(
                        line={'color': '#3498DB', 'width': 4},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None)
                    ).properties(height=300)
                    st.altair_chart(area, use_container_width=True)

                # 4. 경영 전략 제언
                st.markdown(f"""
                    <div style="background-color: {NAVY}; color: white; padding: 2.5rem; border-radius: 15px; margin-top: 2rem; box-shadow: 0 10px 30px rgba(0,31,63,0.1);">
                        <h3 style="color: {GOLD}; margin-bottom: 1rem; font-weight: 700;">💡 공민준 센터장의 경영 전략 제언</h3>
                        <p style="font-size: 1.15rem; line-height: 1.9; opacity: 0.95; white-space: pre-wrap;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 5. 푸터 (프로필 및 명언)
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.divider()
                f1, f2 = st.columns([1, 1])
                with f1:
                    st.markdown(f"""
                        <div style="color: #666; font-size: 0.95rem; line-height: 1.6;">
                            <b style="color: {NAVY}; font-size: 1.1rem;">공민준 센터장</b><br>
                            문의: 010-XXXX-XXXX | SNS7 Business Center<br>
                            보험 분석 및 기업 자금 컨설팅 전문가
                        </div>
                    """, unsafe_allow_html=True)
                with f2:
                    st.markdown("""
                        <div style="text-align: right; font-style: italic; color: #AAA; font-size: 0.95rem; padding-top: 10px;">
                            "성공은 결코 우연이 아니다. 그것은 고된 작업, 인내, 배움, <br>그리고 무엇보다 당신이 하는 일에 대한 사랑의 결과다."
                        </div>
                    """, unsafe_allow_html=True)

            else: st.warning("발행된 경영 리포트가 없습니다. 잠시만 기다려 주세요.")
        except Exception as e: st.error(f"시스템 오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보가 올바르지 않습니다.')
elif st.session_state.get("authentication_status") is None: st.info('CEO 계정 정보를 입력하여 접속해 주세요.')
