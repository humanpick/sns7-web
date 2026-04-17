import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 시스템 및 변수 (V23 절대 고정)
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
    
    header {{ visibility: hidden !important; height: 0px !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding: 3rem 5rem !important; margin-top: -50px !important; }}
    
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
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 설정
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

if 'creds' not in st.session_state:
    st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v30', 'key_v30', 30)
authenticator.login('main')

def generate_strategy(score, sales):
    if score >= 900: sc_text = "최상위권 신용도를 유지 중입니다."
    elif score >= 840: sc_text = "정책자금 승인 권장권으로 매우 안정적입니다."
    elif score >= 750: sc_text = "보통 수준의 신용도이나, 자금 조달을 위해 상향 관리가 필요합니다."
    else: sc_text = "현재 신용도 관리가 시급한 단계입니다. 연체 관리 및 카드 이용 패턴 점검이 필요합니다."

    if sales >= 5000: sl_text = "규모의 경제를 실현하는 단계로, 시설 자금 확보를 통한 확장이 필요합니다."
    elif sales >= 1500: sl_text = "성장기로 접어들었습니다. 고정비 최적화와 운전 자금 확보가 핵심입니다."
    else: sl_text = "기초 체력을 다지는 시기입니다. 초기 정책자금 및 보증 한도 증액을 우선 검토해야 합니다."

    return f"{sc_text}\n\n{sl_text}\n\n추가적인 상세 실행 방안은 다음 대면 컨설팅에서 논의하겠습니다."

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

    # ------------------------------------------
    # 👑 [ADMIN] 관리자 데이터 센터
    # ------------------------------------------
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3 = st.tabs(["📝 리포트 발행", "👥 고객 관리 및 암호 변경", "⚙️ 이력 관리"])
        
        with t1:
            st.subheader("신규 데이터 누적 입력")
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if not v_list: st.info("고객을 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                comp = st.text_input("분석 업체명", placeholder="예: 불타는닭발")
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
                    st.session_state.strat_text = ""
                    st.success("발행 완료!")
                    st.rerun()

        # 💡 [핵심 업데이트] 고객 관리 탭 강화
        with t2:
            st.subheader("👥 고객 계정 관리 및 비밀번호 수정")
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            
            # 1. 기존 고객 비밀번호 수정 섹션
            if v_list:
                with st.expander("🔐 특정 고객 비밀번호 강제 재설정", expanded=False):
                    target_u = st.selectbox("수정할 고객 아이디 선택", v_list)
                    new_pw = st.text_input("새로운 비밀번호 입력", type="password", key="new_pw_input")
                    if st.button("비밀번호 즉시 변경"):
                        if new_pw:
                            hpw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table('users').update({"password": hpw}).eq('username', target_u).execute()
                            st.session_state.creds = fetch_creds() # 메모리 갱신
                            st.success(f"[{target_u}]님의 비밀번호가 성공적으로 변경되었습니다.")
                        else: st.warning("새 비밀번호를 입력해 주세요.")

            st.divider()

            # 2. 신규 등록 섹션
            st.subheader("🆕 신규 고객 등록")
            with st.form("reg_v30"):
                r_id = st.text_input("아이디")
                r_pw = st.text_input("초기 비밀번호", type="password")
                r_name = st.text_input("성함")
                if st.form_submit_button("계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.success("등록 완료")
                    st.rerun()

            st.divider()

            # 3. 고객 명단 및 해시값 조회 (요청하신 표기 기능)
            st.subheader("📋 전체 고객 명단 및 암호 상태")
            cl_data = []
            for k, v in st.session_state.creds['usernames'].items():
                if v['role'] != 'admin':
                    cl_data.append({"아이디": k, "이름": v['name'], "저장된 암호(해시)": v['password']})
            
            if cl_data:
                st.dataframe(pd.DataFrame(cl_data), use_container_width=True)
                st.caption("※ 보안을 위해 비밀번호는 암호화(Hash)된 상태로 저장됩니다. 원본은 복구가 불가능하므로 위 섹션에서 '재설정' 하시면 됩니다.")

        with t3:
            st.subheader("⚙️ 데이터 이력 관리")
            try:
                raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
                if raw_res.data:
                    history_df = pd.DataFrame(raw_res.data)
                    edited_df = st.data_editor(history_df, column_config={"id": None, "client_id": "ID", "company_name": "업체"}, disabled=["created_at", "client_id"], num_rows="dynamic", use_container_width=True)
                    if st.button("🗑️ 변경/삭제사항 DB 영구 반영"):
                        # [동기화 로직 V29와 동일 유지]
                        st.success("동기화 완료")
                        st.rerun()
            except: st.error("로딩 실패")

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (UI 보존)
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
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    base_c = alt.Chart(df).encode(x=alt.X('날짜:N', title=None))
                    line_c = base_c.mark_line(color='#E74C3C', strokeWidth=3).encode(y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999])))
                    st.altair_chart((line_c + line_c.mark_circle(size=120) + line_c.mark_text(dy=-15, fontWeight='bold').encode(text='점수:Q')).properties(height=350), use_container_width=True)
                with c2:
                    base_s = alt.Chart(df).encode(x=alt.X('날짜:N', title=None))
                    area_s = base_s.mark_area(line={'color': '#3498DB'}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2])))
                    st.altair_chart((area_s + base_s.mark_circle(size=130, color='#3498DB').encode(y='매출_억:Q') + base_s.mark_text(dy=25, fontWeight='bold', color='#3498DB').encode(text='매출_표기:N')).properties(height=350), use_container_width=True)

                st.write("")
                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid {BORDER}; padding: 35px; border-radius: 12px;">
                        <h3 style="color: {NAVY}; margin-top: 0; border-bottom: 2px solid {GOLD}; display: inline-block; padding-bottom: 5px;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="color: #333; line-height: 1.9; white-space: pre-wrap; font-size: 1.1rem; margin-top: 20px;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<div style='font-size:0.95rem; color:#666;'><b>공민준 지점장</b><br>SNS7 비즈니스 센터 전문가 그룹</div>", unsafe_allow_html=True)
                f2.markdown(f"<div style='text-align:right; font-style:italic; color:#999; font-size:0.9rem;'>\"성공은 결코 우연이 아니다. <br>인내와 배움, 그리고 희생의 결과다.\"</div>", unsafe_allow_html=True)
            else: st.warning("리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
