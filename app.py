import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 무결성 프로토콜 (V13 Pro UX)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
RED = "#E74C3C"
GREEN = "#27AE60"

st.markdown(f"""
    <div class="notranslate" translate="no">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: #F8F9FA !important;
    }}
    
    header {{ visibility: hidden !important; height: 0px !important; }}
    .block-container {{ padding: 2rem 5rem !important; margin-top: -30px !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 프리미엄 카드 디자인 */
    .metric-card {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-bottom: 4px solid {GOLD};
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center;
    }}
    .metric-label {{ font-size: 0.95rem; color: #7F8C8D; margin-bottom: 0.5rem; font-weight: 400; }}
    .metric-value {{ font-size: 1.8rem; font-weight: 700; color: {NAVY}; }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2rem !important; border-radius: 8px !important;
    }}
    </style>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 (민준 센터장님 정보)
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource(show_spinner=False)
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except:
    st.stop()

# ==========================================
# 2. 데이터 및 인증 코어
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
authenticator = stauth.Authenticate(credentials, 'ceo_portal_v13', 'auth_key_v13', cookie_expiry_days=30)

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

    if user_role == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2 = st.tabs(["📝 데이터 입력", "👥 고객 관리"])
        
        with t1:
            viewer_list = [u for u in all_users if all_users[u].get('role') != 'admin']
            if not viewer_list: st.info("고객을 등록해 주세요.")
            else:
                selected_client = st.selectbox("리포트 대상", viewer_list, format_func=lambda x: f"{all_users[x].get('name')} ({x})")
                with st.form("input_v13"):
                    c_name = st.text_input("업체명")
                    col1, col2 = st.columns(2)
                    score = col1.number_input("신용점수", 300, 1000, 850)
                    sales = col2.number_input("월 매출액(만원)", 0, 100000, 1500)
                    comment = st.text_area("경영 전략 제언")
                    if st.form_submit_button("리포트 발행"):
                        supabase.table('client_data').insert({
                            "client_id": selected_client, "company_name": c_name,
                            "credit_score": str(score), "monthly_sales": str(sales), "strategy_comment": comment
                        }).execute()
                        st.success("발행 완료")
                        st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 프로 프리미엄 리포트
    # ------------------------------------------
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%m-%d')
                df['점수'] = pd.to_numeric(df['credit_score']).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales']).astype(int)
                df['매출_억'] = df['매출'] / 10000.0
                latest = df.iloc[-1]

                # 점수에 따른 동적 상태 설정
                status_color = GREEN if latest['점수'] >= 840 else RED
                status_text = "정책자금 승인 권장" if latest['점수'] >= 840 else "신용 관리 집중 필요"

                # 1. 상단 프리미엄 헤더
                st.markdown(f"""
                    <div style="border-left: 8px solid {GOLD}; padding-left: 20px; margin-bottom: 40px;">
                        <p style="color: #95a5a6; font-size: 0.9rem; letter-spacing: 3px; margin: 0;">SNS7 BUSINESS ANALYTICS</p>
                        <h1 style="color: {NAVY}; font-size: 2.5rem; margin: 5px 0;">{real_name} 대표님 경영 리포트</h1>
                        <p style="color: {status_color}; font-size: 1.1rem; font-weight: 700;">● {status_text}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 2. 메트릭 카드
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-card"><p class="metric-label">분석 업체명</p><p class="metric-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card"><p class="metric-label">최신 신용점수</p><p class="metric-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-card"><p class="metric-label">최근 월 매출</p><p class="metric-value">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # 3. 차트 섹션 (가독성 강화)
                c_col1, c_col2 = st.columns(2)
                
                with c_col1:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; padding-left:10px;">🛡️ 신용점수 추이</p>', unsafe_allow_html=True)
                    # 데이터가 하나일 때도 잘 보이도록 점 크기 확대 및 텍스트 추가
                    base = alt.Chart(df).encode(x=alt.X('날짜:N', title=None))
                    line = base.mark_line(color=RED, strokeWidth=4, interpolate='monotone').encode(y=alt.Y('점수:Q', scale=alt.Scale(domain=[300, 1000]), title=None))
                    points = base.mark_circle(size=150, color=RED).encode(y=alt.Y('점수:Q'))
                    labels = points.mark_text(dy=-20, fontSize=14, fontWeight='bold').encode(text='점수:Q')
                    st.altair_chart((line + points + labels).properties(height=300), use_container_width=True)

                with c_col2:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; padding-left:10px;">💰 매출 성장 곡선 (단위: 억)</p>', unsafe_allow_html=True)
                    area = alt.Chart(df).mark_area(
                        line={{'color': '#3498DB', 'width': 4}},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None)
                    )
                    st.altair_chart(area.properties(height=300), use_container_width=True)

                # 4. 공민준 센터장의 전략 제언 (디자인 강조)
                st.markdown(f"""
                    <div style="background-color: {NAVY}; padding: 3rem; border-radius: 20px; margin-top: 3rem; position: relative; overflow: hidden;">
                        <div style="position: absolute; top: -20px; right: -20px; font-size: 8rem; color: white; opacity: 0.05; font-weight: 700;">“</div>
                        <h3 style="color: {GOLD}; font-size: 1.5rem; margin-bottom: 1.5rem; font-weight: 700;">💡 공민준 센터장의 경영 전략 제언</h3>
                        <p style="color: white; font-size: 1.15rem; line-height: 2; opacity: 0.9; white-space: pre-wrap;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 5. 푸터
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<p style='color:#7f8c8d; font-size:0.9rem;'><b>공민준 센터장</b> | SNS7 비즈니스 센터<br>기업 자금 컨설팅 & 보험 분석 전문가</p>", unsafe_allow_html=True)
                f2.markdown(f"<p style='text-align:right; color:#bdc3c7; font-style:italic; font-size:0.85rem;'>\"비즈니스의 가치는 숫자를 넘어 <br>사람을 향한 진심에서 시작됩니다.\"</p>", unsafe_allow_html=True)

            else: st.warning("발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력해 주세요.')
