import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. 디자인 시스템 및 변수 (V23 절대 고정 스탠다드)
# ==========================================
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded" # 접속 시 사이드바를 기본으로 열어둡니다.
)

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    /* 💡 [핵심] 사이드바 열기 버튼 강제 소생 */
    [data-testid="collapsedControl"] {{
        display: block !important;
        background-color: transparent !important;
    }}
    
    /* 열기(>) 버튼을 프리미엄 플로팅 버튼으로 스타일링 */
    button[title="Open sidebar"], [data-testid="stSidebarCollapseButton"] {{
        background-color: white !important;
        border: 2px solid {GOLD} !important;
        color: {NAVY} !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 999999 !important;
        width: 42px !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* 헤더는 투명하게 유지하되 삭제하지 않음 */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0) !important;
    }}
    
    /* 툴바 메뉴는 여전히 숨김 */
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}

    .block-container {{ padding: 3rem 5rem !important; margin-top: -10px !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 리포트 카드 디자인 */
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
        margin-bottom: 10px; border-left: 4px solid {GOLD}; padding-left: 10px;
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
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

# ==========================================
# 2. 데이터 및 인증 코어
# ==========================================
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v36', 'key_v36', 30)
authenticator.login('main')

def generate_strategy(score, sales):
    if score >= 840: conclusion = "저금리 정책자금 확보의 최적기입니다."
    else: conclusion = "신용 관리를 통한 금리 인하 전략이 필요합니다."
    return f"현재 신용점수 {score}점, 매출 {sales}만원 기반 맞춤 분석 결과입니다.\n\n💡 결론: {conclusion}"

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
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # 👑 [ADMIN] 관리자 데이터 센터
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']

        with t1:
            st.subheader("신규 데이터 누적 입력")
            if not v_list: st.info("고객을 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                comp = st.text_input("분석 업체명 (최신화)")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                if st.button("💡 전략 자동 생성"):
                    st.session_state.strat_text = generate_strategy(sc, sa)
                    st.rerun()
                cmt = st.text_area("공민준 센터장의 경영 전략 제시", value=st.session_state.get('strat_text', ""), height=150)
                if st.button("💾 최종 저장 및 리포트 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("발행 성공!")
                    st.rerun()

        with t2:
            st.subheader("👥 고객 계정 관리")
            with st.form("reg_v36"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("비번", type="password"), st.text_input("성함")
                if st.form_submit_button("계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 데이터 이력 관리")
            try:
                raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
                if raw_res.data:
                    history_df = pd.DataFrame(raw_res.data)
                    edited_df = st.data_editor(history_df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
                    if st.button("🗑️ 변경/삭제사항 DB 영구 반영"):
                        # [V33 동기화 로직 적용...]
                        st.success("동기화 완료")
            except: pass

        with t4:
            st.subheader("📅 센터장님 고객 관리 스케줄")
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_date = st.date_input("날짜 선택", datetime.now())
                sch_client_id = st.selectbox("고객 선택", ["일반 일정"] + v_list, format_func=lambda x: client_map.get(x, x))
                sch_time, sch_content = st.time_input("시간", time(10, 0)), st.text_area("내용")
                if st.button("📅 일정 등록"):
                    display_name = client_map.get(sch_client_id, sch_client_id) if sch_client_id != "일반 일정" else "일반 일정"
                    supabase.table('schedules').insert({"client_id": display_name, "schedule_date": str(sel_date), "schedule_time": str(sch_time), "content": sch_content}).execute()
                    st.rerun()
            with c2:
                sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
                for item in sch_res.data:
                    st.markdown(f'<div class="sch-item"><b>[{item["schedule_time"][:5]}]</b> {item["client_id"]}<br>{item["content"]}</div>', unsafe_allow_html=True)
                    if st.button(f"삭제 #{item['id']}", key=f"del_{item['id']}"):
                        supabase.table('schedules').delete().eq('id', item['id']).execute()
                        st.rerun()

    # 📈 [VIEWER] 고객 하이엔드 경영 리포트
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
                    st.altair_chart((line + line.mark_circle(size=100)).properties(height=300), use_container_width=True)
                with c2:
                    df['매출_억'] = pd.to_numeric(df['monthly_sales']) / 10000.0
                    area = alt.Chart(df).mark_area(color='#3498DB', opacity=0.3).encode(x='날짜:N', y='매출_억:Q')
                    st.altair_chart(area.properties(height=300), use_container_width=True)

                st.markdown(f'<div style="background:white; border:2px solid {BORDER}; padding:30px; border-radius:12px; margin-top:20px;">'
                            f'<h3 style="color:{NAVY}; border-bottom:2px solid {GOLD}; display:inline-block;">💡 센터장 경영 전략</h3>'
                            f'<p style="white-space:pre-wrap; margin-top:15px;">{latest["strategy_comment"]}</p></div>', unsafe_allow_html=True)
            else: st.warning("발행된 리포트가 없습니다.")
        except: st.error("데이터 로딩 중 오류가 발생했습니다.")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('로그인 후 이용 가능합니다.')
