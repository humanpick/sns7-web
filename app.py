import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. [중요] 최상단 배치: 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded" # 접속 시 무조건 열린 상태로 시작
)

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. 강력한 UI/CSS 패치 (사이드바 버튼 소생)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    /* 💡 사이드바 열기 버튼을 화면 맨 위로 강제 인출 */
    [data-testid="collapsedControl"] {{
        display: block !important;
        position: fixed !important;
        z-index: 999999 !important;
        top: 15px !important;
        left: 15px !important;
    }}

    /* 버튼 모양을 황금색 테두리의 프리미엄 스타일로 변경 */
    [data-testid="stSidebarCollapseButton"] {{
        background-color: white !important;
        border: 2px solid {GOLD} !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        width: 45px !important;
        height: 45px !important;
        color: {NAVY} !important;
    }}

    /* 메인 컨텐츠 상단 여백 조정 */
    .block-container {{ padding-top: 4rem !important; }}
    
    /* 사이드바 내부 색상 고정 */
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; min-width: 250px !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 리포트 카드 디자인 */
    .metric-card-v23 {{
        background-color: #FFFFFF !important;
        padding: 22px !important;
        border-radius: 12px !important;
        border: 2px solid {BORDER} !important;
        margin-bottom: 20px !important;
    }}
    .label-v23 {{ 
        font-size: 0.95rem !important; color: #666 !important; font-weight: 700 !important; 
        border-left: 4px solid {GOLD}; padding-left: 10px;
    }}
    .value-v23 {{ font-size: 1.8rem !important; font-weight: 700 !important; color: {NAVY} !important; }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2.5rem !important; border-radius: 6px !important;
    }}
    
    .sch-item {{ 
        background: white; padding: 15px; border-radius: 8px; 
        border-left: 5px solid {GOLD}; margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 연결 설정
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ------------------------------------------
# 데이터 및 인증 로직
# ------------------------------------------
def fetch_creds():
    try:
        res = supabase.table('users').select('*').execute()
        c = {'usernames': {}}
        for u in res.data:
            c['usernames'][str(u['username'])] = {
                'name': str(u['name']), 
                'password': str(u['password']), 
                'role': str(u.get('role', 'viewer'))
            }
        return c
    except: return {'usernames': {}}

def get_client_display_map():
    display_map = {}
    try:
        res = supabase.table('client_data').select('client_id, company_name').order('created_at', desc=True).execute()
        temp_map = {item['client_id']: item['company_name'] for item in res.data}
        for username, info in st.session_state.creds['usernames'].items():
            if info['role'] != 'admin':
                company = temp_map.get(username, "업체 정보 없음")
                display_map[username] = f"{info['name']} | {company}"
    except: pass
    return display_map

if 'creds' not in st.session_state:
    st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v37', 'key_v37', 30)
authenticator.login('main')

# ==========================================
# 3. 메인 화면 출력
# ==========================================
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    # 사이드바 내용 (무조건 렌더링)
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        st.divider()
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # [ADMIN] 관리자 모드
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']

        with t1:
            st.subheader("신규 데이터 입력")
            if v_list:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                comp = st.text_input("업체명")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("매출액(만원)", 0, 100000, 1300)
                cmt = st.text_area("경영 전략 제시", height=150)
                if st.button("💾 발행하기"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("발행 완료!")
                    st.rerun()

        with t4:
            st.subheader("📅 스케줄 관리")
            sel_date = st.date_input("날짜 선택", datetime.now())
            sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
            for item in sch_res.data:
                st.markdown(f'<div class="sch-item"><b>[{item["schedule_time"][:5]}]</b> {item["client_id"]}<br>{item["content"]}</div>', unsafe_allow_html=True)

    # [VIEWER] 고객 리포트 모드 (전체 복구)
    else:
        res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%m-%d')
            latest = df.iloc[-1]
            
            st.markdown(f"<h3 style='color:{GOLD};'>SNS7 BUSINESS ANALYTICS</h3>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='color:{NAVY};'>{real_name} 대표님 경영 리포트</h1>", unsafe_allow_html=True)
            
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">신용점수</p><p class="value-v23">{latest["credit_score"]}점</p></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">월 매출액</p><p class="value-v23">{int(latest["monthly_sales"]):,}만원</p></div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                line = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=3).encode(x='날짜:N', y=alt.Y('credit_score:Q', scale=alt.Scale(domain=[500, 999])))
                st.altair_chart((line + line.mark_circle(size=100)).properties(height=300), use_container_width=True)
            with c2:
                df['매출_억'] = pd.to_numeric(df['monthly_sales']) / 10000.0
                area = alt.Chart(df).mark_area(color='#3498DB', opacity=0.3).encode(x='날짜:N', y='매출_억:Q')
                st.altair_chart(area.properties(height=300), use_container_width=True)

            st.markdown(f'<div style="background:white; border:2px solid {BORDER}; padding:30px; border-radius:12px; margin-top:20px;">'
                        f'<h3 style="color:{NAVY}; border-bottom:2px solid {GOLD}; display:inline-block;">💡 센터장 경영 전략</h3>'
                        f'<p style="white-space:pre-wrap; margin-top:15px;">{latest["strategy_comment"]}</p></div>', unsafe_allow_html=True)
        else: st.warning("발행된 리포트가 없습니다.")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('로그인 후 이용 가능합니다.')
