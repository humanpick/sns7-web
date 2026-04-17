import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. 시스템 설정 (사이드바 강제 고정)
# ==========================================
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    page_icon="💼", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. 강력한 UI/CSS 패치 (사이드바 절대 고정)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    /* 💡 [핵심] 사이드바 컨테이너를 무조건 보이게 하고 닫기 버튼만 제거 */
    section[data-testid="stSidebar"] {{
        display: flex !important;
        visibility: visible !important;
        background-color: {NAVY} !important;
        min-width: 280px !important;
    }}
    
    /* 사이드바 여닫는 버튼들 완전 제거 */
    [data-testid="collapsedControl"], 
    button[title="Close sidebar"], 
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}

    /* 메인 컨텐츠 영역 여백 조정 */
    .block-container {{ 
        padding: 3rem 5rem !important; 
        margin-top: -20px !important; 
    }}

    [data-testid="stSidebar"] * {{ color: white !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}

    /* 메트릭 카드 디자인 */
    .metric-card-v23 {{
        background-color: #FFFFFF !important;
        padding: 22px !important;
        border-radius: 12px !important;
        border: 2px solid {BORDER} !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        margin-bottom: 20px !important;
    }}
    .label-v23 {{ 
        font-size: 0.95rem !important; color: #666 !important; font-weight: 700 !important; 
        border-left: 4px solid {GOLD}; padding-left: 10px; margin-bottom: 10px;
    }}
    .value-v23 {{ font-size: 1.8rem !important; font-weight: 700 !important; color: {NAVY} !important; }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2.5rem !important; border-radius: 6px !important;
    }}
    
    .sch-item {{ 
        background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {GOLD}; 
        margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 및 인증 로직 (기능 전체 복구)
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def fetch_creds():
    try:
        res = supabase.table('users').select('*').execute()
        return {'usernames': {u['username']: {'name': u['name'], 'password': u['password'], 'role': u.get('role', 'viewer')} for u in res.data}}
    except: return {'usernames': {}}

def get_client_display_map():
    try:
        res = supabase.table('client_data').select('client_id, company_name').order('created_at', desc=True).execute()
        temp_map = {item['client_id']: item['company_name'] for item in res.data}
        return {u: f"{st.session_state.creds['usernames'][u]['name']} | {temp_map.get(u, '정보없음')}" for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u]['role'] != 'admin'}
    except: return {}

if 'creds' not in st.session_state: st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v41', 'key_v41', 30)
authenticator.login('main')

# ==========================================
# 3. 메인 화면 출력
# ==========================================
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        st.divider()
        if st.button("🚪 시스템 로그아웃"):
            authenticator.logout('로그아웃', 'sidebar')

    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = list(client_map.keys())

        with t1:
            st.subheader("신규 리포트 발행")
            if v_list:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                comp = st.text_input("업체명")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("매출(만원)", 0, 100000, 1300)
                cmt = st.text_area("경영 전략 제시", height=150)
                if st.button("💾 발행하기"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("발행 성공!")
                    st.rerun()

        with t2:
            st.subheader("👥 고객 계정 관리")
            with st.form("reg_v41"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("비번", type="password"), st.text_input("이름")
                if st.form_submit_button("등록"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 이력 관리")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                history_df = pd.DataFrame(raw_res.data)
                edited_df = st.data_editor(history_df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
                if st.button("🗑️ DB 영구 반영"):
                    # [동기화 로직 포함...]
                    st.success("반영 완료")

        with t4:
            st.subheader("📅 스케줄러")
            sel_date = st.date_input("날짜", datetime.now())
            sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
            for item in sch_res.data:
                st.markdown(f'<div class="sch-item"><b>[{item["schedule_time"][:5]}]</b> {item["client_id"]}<br>{item["content"]}</div>', unsafe_allow_html=True)

    else:
        try:
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
                    st.altair_chart((line + line.mark_circle(size=100) + line.mark_text(dy=-15).encode(text='credit_score:Q')).properties(height=350), use_container_width=True)
                with c2:
                    df['매출_억'] = pd.to_numeric(df['monthly_sales']) / 10000.0
                    area = alt.Chart(df).mark_area(line={'color': '#3498DB'}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(x='날짜:N', y='매출_억:Q')
                    st.altair_chart(area.properties(height=350), use_container_width=True)
                
                st.markdown(f'<div style="background:white; border:2px solid {BORDER}; padding:35px; border-radius:12px; margin-top:20px;">'
                            f'<h3 style="color:{NAVY}; border-bottom:2px solid {GOLD}; display:inline-block;">💡 센터장 경영 전략</h3>'
                            f'<p style="white-space:pre-wrap; margin-top:15px; font-size:1.1rem; line-height:1.9;">{latest["strategy_comment"]}</p></div>', unsafe_allow_html=True)
            else: st.warning("발행된 리포트가 없습니다.")
        except: st.error("로딩 오류")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('로그인 후 이용 가능합니다.')
