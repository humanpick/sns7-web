import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time
import plotly.graph_objects as go  # [추가] 게이지 차트를 위한 라이브러리

# ==========================================
# [불변 메모리] SNS7 하이엔드 UI 표준 (V23-Fixed)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 경영관리", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. UI/CSS 패치
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Pretendard', sans-serif !important; background-color: {BG_COLOR} !important; }}

    [data-testid="collapsedControl"] {{
        background-color: {GOLD} !important; border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        top: 15px !important; left: 15px !important; z-index: 999999 !important; display: flex !important;
    }}
    [data-testid="collapsedControl"] svg {{ fill: {NAVY} !important; color: {NAVY} !important; }}

    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    
    .block-container {{ padding: 3rem 5rem !important; margin-top: -20px !important; }}

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
# [추가] 신용점수 게이지 차트 생성 함수
# ------------------------------------------
def draw_credit_gauge(score):
    # 구간별 텍스트 및 컬러 로직 (710, 745, 839 기준)
    if 710 <= score <= 839:
        status_text = "양방향 수혜 골든존"
        bar_color = GOLD 
    elif score > 839:
        status_text = "우량 기업 전용 지원"
        bar_color = NAVY
    elif score >= 710:
        status_text = "일반 정책자금권"
        bar_color = "#3498DB"
    else:
        status_text = "신용 집중 관리 요망"
        bar_color = "#E74C3C"

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"<span style='font-size:1.1em;color:{NAVY}'><b>현재 상태: {status_text}</b></span><br><span style='font-size:0.8em;color:gray'>NICE 평가정보 기준</span>"},
        number = {'font': {'size': 45, 'color': bar_color, 'weight': 'bold'}, 'suffix': "점"},
        gauge = {
            'axis': {'range': [300, 1000], 'tickwidth': 1, 'tickcolor': BORDER},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': BORDER,
            'steps': [
                {'range': [300, 710], 'color': "#F8F9FA"},
                {'range': [710, 745], 'color': "#E8F0F8"},
                {'range': [745, 839], 'color': "#FFF9E6"}, # 골든존 배경 하이라이트
                {'range': [839, 1000], 'color': "#E6EDF5"}
            ],
            'threshold': {
                'line': {'color': "#E74C3C", 'width': 3},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=320, margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Pretendard"})
    return fig

import streamlit as st
from supabase import create_client

# ------------------------------------------
# 3. 데이터 엔진 코어 (보안 적용 버전)
# ------------------------------------------
# 소스 코드에 직접 적지 않고, Streamlit의 '비밀 금고'에서 정보를 가져옵니다.
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# DB 연결
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
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

cookie_name = "sns7_ceo_cookie"
cookie_key = "sns7_secure_signature_key_2026"
cookie_expiry_days = 30

authenticator = stauth.Authenticate(
    st.session_state.creds, 
    cookie_name, 
    cookie_key, 
    cookie_expiry_days
)

with st.sidebar:
    st.write("### 💼 SNS7 CEO 경영관리")
    st.markdown("<p style='font-size:0.9rem; color:#A0AAB5;'>프리미엄 비즈니스 분석 시스템</p>", unsafe_allow_html=True)
    st.divider()

authenticator.login('main')

def generate_strategy(score, sales):
    if 710 <= score <= 839: conclusion = "저신용 자금과 우량 보증을 동시 공략할 수 있는 양방향 수혜의 골든타임입니다."
    elif score >= 840: conclusion = "1금융권 우량 정책자금 및 협약보증 확보의 최적기입니다."
    else: conclusion = "신용 관리를 통한 자금 조달 리포지셔닝이 우선적으로 필요합니다."
    return f"현재 신용점수 {score}점, 매출액 {sales}만원 기반 센터장 정밀 분석입니다.\n\n💡 결론: {conclusion}\n\n상세 실행 방안은 다음 컨설팅에서 논의하겠습니다."

# ==========================================
# 4. 로그인 검증 및 메인 화면 출력
# ==========================================
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"**{real_name}**님 환영합니다.")
        st.write("")
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
                sc = c1.number_input("신용점수", 300, 1000, 807)
                sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                if st.button("💡 전략 자동 생성"):
                    st.session_state.strat_text = generate_strategy(sc, sa)
                    st.rerun()
                cmt = st.text_area("공민준 센터장의 경영 전략 제시", value=st.session_state.get('strat_text', ""), height=150)
                if st.button("💾 최종 저장 및 발행"):
                    supabase.table('client_data').insert({"client_id": sel_id, "company_name": comp, "credit_score": sc, "monthly_sales": sa, "strategy_comment": cmt}).execute()
                    st.success("리포트가 성공적으로 발행되었습니다.")
                    st.rerun()

        # (t2, t3, t4 기존 코드 생략 없이 동일 유지)
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
            with st.form("reg_v52"):
                r_id, r_pw, r_name = st.text_input("아이디"), st.text_input("초기비번", type="password"), st.text_input("성함")
                if st.form_submit_button("신규 계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.rerun()

        with t3:
            st.subheader("⚙️ 이력 동기화 관리")
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
                current_score = int(latest["점수"])

                st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>SNS7 BUSINESS ANALYTICS</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color:{NAVY}; margin-top:0; font-size:2.5rem;'>{real_name} 대표님 경영 분석 리포트</h1>", unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{current_score}점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{latest["매출"]:,}만원</p></div>', unsafe_allow_html=True)

                # ==========================================
                # [추가] 실시간 자금 조달 게이지 & 해설 블록
                # ==========================================
                g_col1, g_col2 = st.columns([1.2, 1])
                with g_col1:
                    st.markdown(f"**🎯 실시간 정책자금 가용성 진단**")
                    st.plotly_chart(draw_credit_gauge(current_score), use_container_width=True)
                
                with g_col2:
                    st.markdown(f"""
                    <div style="background-color: white; border: 1px solid {BORDER}; padding: 25px; border-radius: 12px; height: 320px; display:flex; flex-direction:column; justify-content:center;">
                        <h4 style="color:{NAVY}; margin-top:0; margin-bottom:15px;">📊 구간별 확보 가능 자금</h4>
                        <ul style="line-height:2.0; color:#444; font-size:1.0rem; padding-left:20px;">
                            <li><b>~ 839점:</b> 신용취약 소상공인자금 <span style="color:red; font-size:0.8rem;">(안전장치)</span></li>
                            <li><b>710점 ~:</b> 골목상권 보증, 성장유망 특화보증</li>
                            <li><b>745점 ~:</b> 기업가형 소상공인 육성 협약보증</li>
                        </ul>
                        <div style="margin-top:15px; padding:15px; background-color:#FFF9E6; border-left:4px solid {GOLD}; border-radius:4px; font-size:0.95rem;">
                            <b>✅ 센터장 코멘트</b><br>
                            대표님의 현재 점수에 맞춰 가장 유리한 정부 지원금을 우선 배정하여 맞춤형 컨설팅을 진행합니다.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

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
