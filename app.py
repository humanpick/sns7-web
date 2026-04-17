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
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Pretendard', sans-serif !important; background-color: {BG_COLOR} !important; }}
    header {{ visibility: hidden !important; height: 0px !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding: 3rem 5rem !important; margin-top: -50px !important; }}
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    .metric-card-v23 {{
        background-color: #FFFFFF !important; padding: 22px !important; border-radius: 12px !important;
        border: 2px solid {BORDER} !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important; margin-bottom: 20px !important;
    }}
    .label-v23 {{ font-size: 0.95rem !important; color: #666 !important; font-weight: 700 !important; margin-bottom: 10px; border-left: 4px solid {GOLD}; padding-left: 10px; }}
    .value-v23 {{ font-size: 1.8rem !important; font-weight: 700 !important; color: {NAVY} !important; }}
    .stButton>button {{ background-color: {GOLD} !important; color: {NAVY} !important; border: none !important; font-weight: 700 !important; padding: 0.6rem 2.5rem !important; border-radius: 6px !important; }}
    
    .sch-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {GOLD}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
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

# 💡 고객ID를 [성함 | 업체명]으로 변환하는 헬퍼 함수
def get_client_display_map():
    display_map = {}
    try:
        # 모든 고객의 최신 업체명 정보를 가져옴
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v32', 'key_v32', 30)
authenticator.login('main')

def generate_strategy(score, sales):
    # (기존 전략 생성 로직 동일)
    return f"현재 점수({score})와 매출({sales}) 기반 전략 분석 중..."

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

    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        # 최신 고객 매핑 정보 가져오기
        client_map = get_client_display_map()
        v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']

        with t1:
            st.subheader("신규 데이터 누적 입력")
            if v_list:
                # 💡 [개선] 선택 창에서 성함과 상호가 같이 보입니다.
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                comp = st.text_input("분석 업체명 (최신화)")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                if st.button("💾 저장 및 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": "분석중"}).execute()
                    st.success("발행 완료")
                    st.rerun()

        with t4:
            st.subheader("📅 센터장님 고객 관리 스케줄")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                sel_date = st.date_input("날짜 선택", datetime.now())
                st.write("---")
                with st.container():
                    # 💡 [개선] 스케줄 입력 시에도 성함과 상호로 고객 선택
                    sch_client_id = st.selectbox("관련 고객 선택", ["일반 일정"] + v_list, format_func=lambda x: client_map.get(x, x))
                    sch_time = st.time_input("시간", time(10, 0))
                    sch_content = st.text_area("일정 내용")
                    
                    if st.button("📅 일정 등록"):
                        display_name = client_map.get(sch_client_id, sch_client_id) if sch_client_id != "일반 일정" else "일반 일정"
                        supabase.table('schedules').insert({
                            "client_id": display_name, # 💡 [개선] DB에도 식별하기 좋게 저장
                            "schedule_date": str(sel_date),
                            "schedule_time": str(sch_time),
                            "content": sch_content
                        }).execute()
                        st.rerun()

            with c2:
                st.write(f"### 3. {sel_date} 상세 스케줄")
                sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
                if sch_res.data:
                    for item in sch_res.data:
                        st.markdown(f"""
                            <div class="sch-item">
                                <span style="color:{GOLD}; font-weight:bold;">[{item['schedule_time'][:5]}]</span> 
                                <span style="color:{NAVY}; font-weight:bold;">{item['client_id']}</span><br>
                                <div style="margin-top:5px; color:#333;">{item['content']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"삭제 #{item['id']}", key=f"del_{item['id']}"):
                            supabase.table('schedules').delete().eq('id', item['id']).execute()
                            st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] (기존 UI 보존)
    # ------------------------------------------
    else:
        # (기존 Viewer 코드와 동일)
        pass

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
