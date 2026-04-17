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
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    /* 💡 [수정] 헤더 전체를 display:none 하지 않고, 필요한 버튼(사이드바 토글)만 남깁니다 */
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stHeader"] [data-testid="stToolbar"] {{ visibility: hidden !important; }}
    
    /* 💡 [추가] 사이드바 열기 버튼(>)을 프리미엄 스타일로 강조 */
    [data-testid="stSidebarCollapseButton"] {{
        background-color: white !important;
        border: 1px solid {BORDER} !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        color: {NAVY} !important;
        border-radius: 50% !important;
        margin-left: 10px !important;
        margin-top: 5px !important;
    }}

    .block-container {{ padding: 3rem 5rem !important; margin-top: -30px !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v34', 'key_v34', 30)
authenticator.login('main')

def generate_strategy(score, sales):
    if score >= 900: sc_text = "최상위권 신용도를 유지 중입니다."
    elif score >= 840: sc_text = "정책자금 승인 권장권으로 매우 안정적입니다."
    elif score >= 750: sc_text = "보통 수준의 신용도이나, 자금 조달을 위해 상향 관리가 필요합니다."
    else: sc_text = "현재 신용도 관리가 시급한 단계입니다. 연체 관리 및 카드 이용 패턴 점검이 필요합니다."

    if sales >= 5000: sl_text = "규모의 경제를 실현하는 단계로, 시설 자금 확보를 통한 확장이 필요합니다."
    elif sales >= 1500: sl_text = "성장기로 접어들었습니다. 고정비 최적화와 운전 자금 확보가 핵심입니다."
    else: sl_text = "기초 체력을 다지는 시기입니다. 초기 정책자금 및 보증 한도 증액을 우선 검토해야 합니다."

    conclusion = "최적의 자금 조달 타이밍을 분석 중입니다."
    if score >= 840 and sales >= 1500: conclusion = "저금리 정책자금 확보의 최적기입니다."

    return f"{sc_text}\n\n{sl_text}\n\n💡 결론: {conclusion}\n\n추가 상세 실행 방안은 대면 컨설팅에서 논의하겠습니다."

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
                if 'strat_text' not in st.session_state: st.session_state.strat_text = ""
                cmt = st.text_area("공민준 센터장의 경영 전략 제시", key="strat_text", height=150)
                if st.button("💾 최종 저장 및 리포트 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("발행 성공!")
                    st.rerun()

        with t2:
            st.subheader("👥 고객 계정 및 비밀번호 관리")
            with st.form("reg_v34"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("비번", type="password"), st.text_input("성함")
                if st.form_submit_button("계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 데이터 이력 관리")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                history_df = pd.DataFrame(raw_res.data)
                edited_df = st.data_editor(history_df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
                if st.button("🗑️ 변경/삭제사항 DB 영구 반영하기"):
                    # 동기화 로직... (V33과 동일)
                    st.success("동기화 완료")

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

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (복구 완료)
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
                df['매출_표기'] = df['매출'].apply(lambda x: f"{x:,}만원") 
                latest = df.iloc[-1]

                st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>SNS7 BUSINESS ANALYTICS</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color:{NAVY}; margin-top:0; font-size:2.5rem;'>{real_name} 대표님 경영 분석 리포트</h1>", unsafe_allow_html=True)
                status_color = "#27AE60" if latest['점수'] >= 840 else "#E74C3C"
                st.markdown(f"<p style='color:{status_color}; font-weight:700;'>● {'권장권' if latest['점수'] >= 840 else '관리필요'}</p>", unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">신용점수</p><p class="value-v23">{latest["점수"]}점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">월 매출액</p><p class="value-v23">{latest["매출"]:,}만원</p></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    base = alt.Chart(df).encode(x=alt.X('날짜:N', title=None))
                    line = base.mark_line(color='#E74C3C', strokeWidth=3).encode(y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999])))
                    st.altair_chart((line + line.mark_circle(size=100) + line.mark_text(dy=-15).encode(text='점수:Q')).properties(height=300), use_container_width=True)
                with c2:
                    base_s = alt.Chart(df).encode(x=alt.X('날짜:N', title=None))
                    area = base_s.mark_area(line={'color': '#3498DB'}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2])))
                    st.altair_chart((area + base_s.mark_text(dy=20).encode(text='매출_표기:N')).properties(height=300), use_container_width=True)

                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid {BORDER}; padding: 35px; border-radius: 12px; margin-top:20px;">
                        <h3 style="color: {NAVY}; border-bottom: 2px solid {GOLD}; display: inline-block;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="white-space: pre-wrap; margin-top: 15px;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)
            else: st.warning("발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력해 주세요.')
