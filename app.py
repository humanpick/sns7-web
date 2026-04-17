import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# [불변 메모리] SNS7 하이엔드 UI 표준 (V23-Fixed)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. 하이브리드 반응형 & 사이드바 제어 CSS
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Pretendard', sans-serif !important; background-color: {BG_COLOR} !important; }}

    /* 🖥️ [PC용] 사이드바 철제 고정 */
    @media (min-width: 992px) {{
        section[data-testid="stSidebar"] {{
            transform: none !important; transition: none !important;
            display: flex !important; visibility: visible !important;
            width: 280px !important; min-width: 280px !important; left: 0 !important;
        }}
        [data-testid="collapsedControl"], button[title="Close sidebar"] {{ display: none !important; }}
        .main .block-container {{ margin-left: 20px !important; }}
    }}

    /* 📱 [모바일용] 자동 숨김 및 황금 버튼 활성화 */
    @media (max-width: 991px) {{
        [data-testid="collapsedControl"] {{
            display: block !important;
            background-color: {NAVY} !important;
            border: 2px solid {GOLD} !important;
            border-radius: 8px !important;
            top: 15px !important; left: 15px !important; z-index: 999999 !important;
        }}
    }}

    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}

    /* 명품 메트릭 카드 */
    .metric-card-v23 {{
        background-color: #FFFFFF !important; padding: 22px !important; border-radius: 12px !important;
        border: 2px solid {BORDER} !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important; margin-bottom: 20px !important;
    }}
    .label-v23 {{ font-size: 0.95rem !important; color: #666 !important; font-weight: 700 !important; border-left: 4px solid {GOLD}; padding-left: 10px; margin-bottom: 10px; }}
    .value-v23 {{ font-size: 1.8rem !important; font-weight: 700 !important; color: {NAVY} !important; }}
    .stButton>button {{ background-color: {GOLD} !important; color: {NAVY} !important; border: none !important; font-weight: 700 !important; padding: 0.6rem 2.5rem !important; border-radius: 6px !important; }}
    .sch-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {GOLD}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333; }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# 3. 데이터 엔진 코어
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
        return {u: f"{st.session_state.creds['usernames'][u]['name']} | {temp_map.get(u, '업체정보없음')}" for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u]['role'] != 'admin'}
    except: return {}

if 'creds' not in st.session_state: st.session_state.creds = fetch_creds()

# 💡 [버그 해결] 쿠키 설정 유지 및 문법 에러 유발 코드 원천 제거
authenticator = stauth.Authenticate(
    st.session_state.creds,
    'sns7_ceo_cookie', # 자동 로그인을 위한 쿠키 이름
    'sns7_signature_key', # 보안 서명 키
    30 # 로그인 유지 기간 (30일)
)

# 군더더기 없이 깔끔하게 로그인 창만 호출합니다. (에러의 원인 완전 제거)
authenticator.login()

def generate_strategy(score, sales):
    if score >= 840: conclusion = "저금리 정책자금 확보의 최적기입니다."
    else: conclusion = "신용 관리를 통한 자금 조달 리포지셔닝이 필요합니다."
    return f"현재 신용점수 {score}점, 매출액 {sales}만원 기반 센터장 정밀 분석입니다.\n\n💡 결론: {conclusion}\n\n상세 실행 방안은 다음 컨설팅에서 논의하겠습니다."

# ==========================================
# 4. 로그인 검증 및 메인 화면 출력
# ==========================================
# Session State를 직접 참조하여 가장 안정적으로 로그인 상태를 확인합니다.
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        st.divider()
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # 👑 [ADMIN] 관리자 데이터 센터
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = list(client_map.keys())

        with t1:
            st.subheader("신규 리포트 발행")
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
                if st.button("💾 최종 저장 및 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("리포트가 성공적으로 발행되었습니다.")
                    st.rerun()

        with t2:
            st.subheader("👥 고객 계정 및 비밀번호 관리")
            if v_list:
                with st.expander("🔐 특정 고객 비밀번호 강제 재설정"):
                    target_u = st.selectbox("수정 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                    new_pw = st.text_input("새 비밀번호 입력", type="password")
                    if st.button("비밀번호 즉시 변경"):
                        hpw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        supabase.table('users').update({"password": hpw}).eq('username', target_u).execute()
                        st.session_state.creds = fetch_creds()
                        st.success("비밀번호가 변경되었습니다.")
            st.divider()
            with st.form("reg_v49"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("초기비번", type="password"), st.text_input("성함")
                if st.form_submit_button("신규 계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 이력 동기화 관리 (삭제/수정)")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                history_df = pd.DataFrame(raw_res.data)
                edited_df = st.data_editor(history_df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
                if st.button("🗑️ 변경/삭제사항 DB 영구 반영"):
                    original_times = set(history_df['created_at'].tolist())
                    current_times = set(edited_df['created_at'].tolist())
                    for d_t in (original_times - current_times):
                        supabase.table('client_data').delete().eq('created_at', d_t).execute()
                    for _, row in edited_df.iterrows():
                        supabase.table('client_data').update({"company_name": row['company_name'], "credit_score": int(row['credit_score']), "monthly_sales": int(row['monthly_sales']), "strategy_comment": str(row['strategy_comment'])}).eq('created_at', row['created_at']).execute()
                    st.success("데이터베이스 동기화 완료")
                    st.rerun()

        with t4:
            st.subheader("📅 센터 스케줄러")
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_date = st.date_input("날짜 선택", datetime.now())
                sch_client_id = st.selectbox("관련 고객", ["일반 일정"] + v_list, format_func=lambda x: client_map.get(x, x))
                sch_time, sch_content = st.time_input("시간", time(10, 0)), st.text_area("일정 내용")
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

    # 📈 [VIEWER] 하이엔드 경영 리포트
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
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{latest["점수"]}점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{latest["매출"]:,}만원</p></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🛡️ 신용점수 분석 추이 (최고 999점)**")
                    base_c = alt.Chart(df).encode(x=alt.X('날짜:N', title=None, axis=alt.Axis(labelAngle=0)))
                    line_c = base_c.mark_line(color='#E74C3C', strokeWidth=3).encode(y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999]), title=None))
                    points_c = base_c.mark_circle(size=120, color='#E74C3C').encode(y='점수:Q')
                    labels_c = points_c.mark_text(dy=-15, fontWeight='bold', fontSize=13).encode(text='점수:Q')
                    st.altair_chart((line_c + points_c + labels_c).properties(height=350), use_container_width=True)

                with c2:
                    st.markdown(f"**💰 매출 성장 곡선 (단위: 억)**")
                    base_s = alt.Chart(df).encode(x=alt.X('날짜:N', title=None, axis=alt.Axis(labelAngle=0)))
                    area_s = base_s.mark_area(
                        line={'color': '#3498DB', 'width': 3},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None))
                    points_s = base_s.mark_circle(size=130, color='#3498DB').encode(y='매출_억:Q')
                    labels_s = points_s.mark_text(dy=25, fontSize=13, fontWeight='bold', color='#3498DB').encode(text='매출_표기:N')
                    st.altair_chart((area_s + points_s + labels_s).properties(height=350), use_container_width=True)

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
        except: st.error("데이터 로딩 오류")

elif st.session_state.get("authentication_status") is False:
    st.error('아이디나 비밀번호가 일치하지 않습니다.')

elif st.session_state.get("authentication_status") is None:
    st.info('💡 **[관리자 안내]** 자동 로그인을 위해 로그인 시 **Remember me** 체크박스를 꼭 클릭해 주세요!')
