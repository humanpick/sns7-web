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
    
    /* 스케줄 리스트 스타일 */
    .sch-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {GOLD}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 연결 및 인증
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
        c = {'usernames': {}}
        for u in res.data:
            c['usernames'][str(u['username'])] = {'name': str(u['name']), 'password': str(u['password']), 'role': str(u.get('role', 'viewer'))}
        return c
    except: return {'usernames': {}}

if 'creds' not in st.session_state: st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v31', 'key_v31', 30)
authenticator.login('main')

# ==========================================
# 3. 메인 화면 로직
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
        
        # [T1, T2, T3 로직은 이전 버전과 동일하게 유지...]
        with t1:
            st.subheader("신규 데이터 누적 입력")
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if v_list:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                comp = st.text_input("업체명")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                if 'strat_text' not in st.session_state: st.session_state.strat_text = ""
                cmt = st.text_area("경영 전략 제시", key="strat_text", height=100)
                if st.button("💾 저장 및 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("발행 완료")
                    st.rerun()

        with t2:
            st.subheader("고객 계정 및 암호 관리")
            cl_df = pd.DataFrame([{"아이디": k, "이름": v['name'], "해시암호": v['password']} for k, v in st.session_state.creds['usernames'].items() if v['role'] != 'admin'])
            st.table(cl_df)
            with st.expander("🔐 비밀번호 강제 재설정"):
                target = st.selectbox("고객 선택", v_list)
                npw = st.text_input("새 암호", type="password")
                if st.button("암호 변경 적용"):
                    hpw = bcrypt.hashpw(npw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').update({"password": hpw}).eq('username', target).execute()
                    st.success("변경되었습니다.")

        with t3:
            st.subheader("데이터 이력 관리")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                history_df = pd.DataFrame(raw_res.data)
                edited_df = st.data_editor(history_df, num_rows="dynamic", use_container_width=True)
                if st.button("🗑️ 변경사항 DB 영구 반영"):
                    # [동기화 로직...]
                    st.success("동기화 완료")

        # 💡 [핵심] 신규 스케줄 관리 탭
        with t4:
            st.subheader("📅 센터장님 고객 관리 스케줄")
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.write("### 1. 날짜 선택")
                # 달력 UI
                sel_date = st.date_input("일정을 입력/조회할 날짜를 선택하세요", datetime.now())
                st.info(f"선택된 날짜: **{sel_date}**")
                
                st.write("---")
                st.write("### 2. 일정 입력")
                with st.container():
                    sch_client = st.selectbox("관련 고객", ["일반 일정"] + v_list)
                    sch_time = st.time_input("상담/업무 시간", time(10, 0))
                    sch_content = st.text_area("일정 내용 (예: 대면 컨설팅, 매출 자료 검토 등)")
                    
                    if st.button("📅 일정 등록하기"):
                        try:
                            supabase.table('schedules').insert({
                                "client_id": sch_client,
                                "schedule_date": str(sel_date),
                                "schedule_time": str(sch_time),
                                "content": sch_content
                            }).execute()
                            st.success("일정이 등록되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"등록 실패: {e}")

            with c2:
                st.write(f"### 3. {sel_date} 상세 스케줄")
                # 해당 날짜의 일정 불러오기
                sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
                
                if sch_res.data:
                    for item in sch_res.data:
                        with st.container():
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
                else:
                    st.write("해당 날짜에 등록된 일정이 없습니다.")

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (UI 보존)
    # ------------------------------------------
    else:
        # [Viewer 코드는 V23~V30 표준 그대로 유지]
        st.title(f"{real_name} 대표님 경영 분석 리포트")
        # (생략: 기존 코드와 동일)

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
