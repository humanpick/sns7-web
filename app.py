import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 및 레이아웃 설정 (클린 & 노멀)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"

# 💡 [해결] 코드 노출을 막기 위해 가장 안전한 방식으로 CSS를 주입합니다.
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
    }}
    
    /* 상단 헤더 및 불필요한 여백 제거 */
    header {{ visibility: hidden !important; height: 0px !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding: 3rem 5rem !important; margin-top: -50px !important; }}
    
    /* 사이드바 색상 고정 */
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 버튼 스타일 */
    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.5rem 2rem !important; border-radius: 5px !important;
    }}
    
    /* 탭 디자인 정돈 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{ font-weight: 700; font-size: 1.1rem; }}
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
# 2. 데이터 및 인증 로직 (동적 갱신 포함)
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

# 세션에 인증 정보 저장
if 'creds' not in st.session_state:
    st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v19', 'key_v19', 30)
authenticator.login('main')

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
        t1, t2 = st.tabs(["📝 리포트 발행", "👥 고객 관리"])
        
        with t1:
            # 💡 리포트 발행 대상 리스트 (관리자 제외)
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if not v_list: 
                st.info("등록된 고객이 없습니다. '고객 관리' 탭에서 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("리포트 대상 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                with st.form("report_input_form"):
                    comp = st.text_input("분석 업체명 (예: 불타는닭발)")
                    c1, c2 = st.columns(2)
                    sc = c1.number_input("신용점수", 300, 1000, 850)
                    sa = c2.number_input("월 매출액(단위: 만원)", 0, 100000, 1300)
                    cmt = st.text_area("공민준 센터장의 경영 전략 제시")
                    if st.form_submit_button("리포트 발행하기"):
                        supabase.table('client_data').insert({
                            "client_id": sel_id, "company_name": comp,
                            "credit_score": str(sc), "monthly_sales": str(sa), "strategy_comment": cmt
                        }).execute()
                        st.success(f"{st.session_state.creds['usernames'][sel_id]['name']}님께 리포트가 전송되었습니다.")
                        st.rerun()

        with t2:
            # 💡 [복구] 고객 등록 폼 및 리스트 출력 로직
            st.subheader("신규 고객 계정 생성")
            with st.form("customer_reg_form"):
                reg_id = st.text_input("1. 희망 아이디 (ID)")
                reg_pw = st.text_input("2. 비밀번호 설정 (PW)", type="password")
                reg_name = st.text_input("3. 고객 성함")
                reg_phone = st.text_input("4. 휴대폰 번호 (숫자만)")
                
                if st.form_submit_button("고객 정보 저장 및 등록"):
                    if not reg_id or not reg_pw or not reg_name:
                        st.warning("필수 항목(ID, 비번, 성함)을 입력해 주세요.")
                    elif reg_id in st.session_state.creds['usernames']:
                        st.error("이미 존재하는 아이디입니다.")
                    else:
                        hpw = bcrypt.hashpw(reg_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        supabase.table('users').insert({
                            "username": reg_id, "name": reg_name, "password": hpw, "role": "viewer"
                        }).execute()
                        # 데이터 즉시 갱신
                        st.session_state.creds = fetch_creds()
                        st.success(f"✅ {reg_name} 대표님 등록 완료!")
                        st.rerun()
            
            st.divider()
            st.subheader("현재 등록된 고객 리스트")
            # 💡 [복구] 저장된 고객 리스트 표기
            all_clients = [{"ID": k, "이름": v['name']} for k, v in st.session_state.creds['usernames'].items() if v['role'] != 'admin']
            if all_clients:
                st.table(pd.DataFrame(all_clients))
            else:
                st.info("등록된 고객 정보가 없습니다.")

    # ------------------------------------------
    # 📈 [VIEWER] 고객 리포트 화면
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

                # 타이틀
                st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>SNS7 비즈니스 분석</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color:{NAVY}; margin-top:0;'>{real_name} 대표님 경영 분석 리포트</h1>", unsafe_allow_html=True)
                status_msg = '신용 관리 집중 필요' if latest['점수'] < 840 else '정책자금 승인 권장권'
                st.markdown(f"<p style='color:#E74C3C; font-weight:700;'>● {status_msg}</p>", unsafe_allow_html=True)

                st.write("")

                # 지표 요약 (표준 메트릭)
                col1, col2, col3 = st.columns(3)
                col1.metric("분석 업체명", latest['company_name'])
                col2.metric("최신 신용점수", f"{latest['점수']} 점")
                col3.metric("최근 월 매출액", f"{latest['매출']:,} 만원")

                st.write("")

                # 차트 섹션
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🛡️ 신용점수 분석 추이**")
                    base_c = alt.Chart(df).encode(x=alt.X('날짜:N', title=None, axis=alt.Axis(labelAngle=0)))
                    line_c = base_c.mark_line(color='#E74C3C', strokeWidth=3).encode(y=alt.Y('점수:Q', scale=alt.Scale(domain=[300, 1000]), title=None))
                    points_c = base_c.mark_circle(size=100, color='#E74C3C').encode(y='점수:Q')
                    labels_c = points_c.mark_text(dy=-15, fontWeight='bold').encode(text='점수:Q')
                    st.altair_chart((line_c + points_c + labels_c).properties(height=300), use_container_width=True)

                with c2:
                    st.markdown(f"**💰 매출 성장 곡선 (단위: 억)**")
                    base_s = alt.Chart(df).encode(x=alt.X('날짜:N', title=None, axis=alt.Axis(labelAngle=0)))
                    area_s = base_s.mark_area(
                        line={'color': '#3498DB', 'width': 3},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None))
                    points_s = base_s.mark_circle(size=120, color='#3498DB').encode(y='매출_억:Q')
                    labels_s = points_s.mark_text(dy=-20, fontSize=13, fontWeight='bold', color='#3498DB').encode(text='매출_표기:N')
                    st.altair_chart((area_s + points_s + labels_s).properties(height=300), use_container_width=True)

                # 전략 제시 박스
                st.write("")
                st.info(f"💡 **공민준 센터장의 경영 전략 제시**\n\n{latest['strategy_comment']}")

                st.divider()
                st.caption("공민준 센터장 | SNS7 비즈니스 센터 | 금융 자금 컨설팅 전문가")

            else: st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"데이터 로딩 중 오류 발생: {e}")

elif st.session_state.get("authentication_status") is False: st.error('아이디 또는 비밀번호가 틀렸습니다.')
elif st.session_state.get("authentication_status") is None: st.info('CEO 계정 정보를 입력하여 접속해 주세요.')
