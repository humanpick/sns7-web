import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. 시스템 설정 (사이드바 강제 고정 모드)
# ==========================================
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    page_icon="💼", 
    layout="wide", 
    initial_sidebar_state="expanded" # 시작 시 확장 상태
)

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. 강력한 UI/CSS 패치 (사이드바 숨김 버튼 완전 제거)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    /* 💡 [핵심] 사이드바를 닫거나 여는 모든 버튼을 아예 제거하여 고정시킴 */
    [data-testid="collapsedControl"], 
    button[title="Close sidebar"], 
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}

    /* 사이드바 너비 고정 및 배경색 */
    [data-testid="stSidebar"] {{ 
        background-color: {NAVY} !important; 
        min-width: 280px !important;
        max-width: 280px !important;
    }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 헤더 및 툴바 제거 */
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}

    .block-container {{ padding: 3rem 5rem !important; margin-top: -10px !important; }}

    /* 메트릭 카드 V23 표준 */
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 및 인증 핵심 로직 (이전 기능 전체 복구)
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v40', 'key_v40', 30)
authenticator.login('main')

def generate_strategy(score, sales):
    if score >= 840: conclusion = "저금리 정책자금 확보의 최적기입니다."
    else: conclusion = "신용 관리를 통한 금리 인하 전략이 시급합니다."
    return f"현재 신용 {score}점, 매출 {sales}만원 기반 맞춤 분석입니다.\n\n💡 결론: {conclusion}\n\n상세 실행 방안은 대면 컨설팅에서 논의하겠습니다."

# ==========================================
# 3. 메인 화면 출력 (모든 기능 통합)
# ==========================================
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        st.divider()
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # [ADMIN] 관리자 데이터 센터 (모든 탭 복구)
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = list(client_map.keys())

        with t1:
            st.subheader("신규 데이터 누적 입력")
            if v_list:
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
                    st.success("리포트가 발행되었습니다!")
                    st.rerun()

        with t2:
            st.subheader("👥 고객 계정 관리 및 암호 수정")
            if v_list:
                with st.expander("🔐 특정 고객 비밀번호 강제 재설정"):
                    target_u = st.selectbox("수정할 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                    new_pw = st.text_input("새 비밀번호", type="password")
                    if st.button("비밀번호 즉시 변경"):
                        hpw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        supabase.table('users').update({"password": hpw}).eq('username', target_u).execute()
                        st.session_state.creds = fetch_creds()
                        st.success("변경 완료")
            st.divider()
            with st.form("reg_v40"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("비번", type="password"), st.text_input("성함")
                if st.form_submit_button("신규 고객 계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 데이터 이력 관리 (DB 동기화)")
            try:
                raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
                if raw_res.data:
                    history_df = pd.DataFrame(raw_res.data)
                    edited_df = st.data_editor(history_df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
                    if st.button("🗑️ 변경/삭제사항 DB 영구 반영하기"):
                        original_times = set(history_df['created_at'].tolist())
                        current_times = set(edited_df['created_at'].tolist())
                        for d_time in (original_times - current_times):
                            supabase.table('client_data').delete().eq('created_at', d_time).execute()
                        for idx, row in edited_df.iterrows():
                            supabase.table('client_data').update({"company_name": row['company_name'], "credit_score": int(row['credit_score']), "monthly_sales": int(row['monthly_sales']), "strategy_comment": str(row['strategy_comment'])}).eq('created_at', row['created_at']).execute()
                        st.success("데이터베이스 동기화 완료")
                        st.rerun()
            except: pass

        with t4:
            st.subheader("📅 스케줄 관리")
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
                    if st.button(f"삭제 #{item['id']}", key=f"ds_{item['id']}"):
                        supabase.table('schedules').delete().eq('id', item['id']).execute()
                        st.rerun()

    # 📈 [VIEWER] 하이엔드 경영 리포트 (V23 원복 완료)
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%m-%d')
                latest = df.iloc[-1]
                
                st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>SNS7 BUSINESS ANALYTICS</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color:{NAVY}; margin-top:0; font-size:2.5rem;'>{real_name} 대표님 경영 분석 리포트</h1>", unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{latest["credit_score"]}점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{int(latest["monthly_sales"]):,}만원</p></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🛡️ 신용점수 분석 추이 (최고 999점)**")
                    line = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=3).encode(x='날짜:N', y=alt.Y('credit_score:Q', scale=alt.Scale(domain=[500, 999]), title=None))
                    points = line.mark_circle(size=120, color='#E74C3C')
                    labels = points.mark_text(dy=-15, fontWeight='bold', fontSize=13).encode(text='credit_score:Q')
                    st.altair_chart((line + points + labels).properties(height=350), use_container_width=True)
                with c2:
                    st.markdown(f"**💰 매출 성장 곡선 (단위: 억)**")
                    df['매출_억'] = pd.to_numeric(df['monthly_sales']) / 10000.0
                    area = alt.Chart(df).mark_area(line={'color': '#3498DB', 'width': 3}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(x='날짜:N', y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None))
                    st.altair_chart(area.properties(height=350), use_container_width=True)

                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid {BORDER}; padding: 35px; border-radius: 12px; margin-top:20px;">
                        <h3 style="color: {NAVY}; border-bottom: 2px solid {GOLD}; display: inline-block; padding-bottom: 5px;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="white-space: pre-wrap; line-height: 1.9; font-size: 1.1rem; margin-top: 15px;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<div style='font-size:0.95rem; color:#666;'><b>공민준 지점장</b><br>SNS7 비즈니스 센터 전문가 그룹</div>", unsafe_allow_html=True)
                f2.markdown(f"<div style='text-align:right; font-style:italic; color:#999; font-size:0.9rem;'>\"성공은 결코 우연이 아니다. <br>인내와 배움, 그리고 희생의 결과다.\"</div>", unsafe_allow_html=True)
            else: st.warning("발행된 리포트가 없습니다.")
        except: st.error("데이터 로딩 중 오류가 발생했습니다.")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
