import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 무결성 프로토콜 (CSS 코드 노출 완벽 차단)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# 💡 [핵심 해결] 스타일 시트를 별도 변수로 정의하고 중괄호를 이중{{ }}로 처리하여 
# 상단에 코드가 텍스트로 뜨는 현상을 완전히 해결했습니다.
NAVY = "#001F3F"
GOLD = "#D4AF37"

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: #F8F9FA !important;
    }}
    
    header {{ visibility: hidden !important; height: 0px !important; }}
    .block-container {{ padding: 2rem 5rem !important; margin-top: -30px !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    .metric-card {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-bottom: 4px solid {GOLD};
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center;
    }}
    .metric-label {{ font-size: 0.95rem; color: #7F8C8D; margin-bottom: 0.5rem; }}
    .metric-value {{ font-size: 1.8rem; font-weight: 700; color: {NAVY}; }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2rem !important; border-radius: 8px !important;
    }}
</style>
<meta name="google" content="notranslate">
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 설정
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ==========================================
# 2. 데이터 및 인증 코어 (Unhashable 에러 방지)
# ==========================================

# 💡 [핵심 해결] 딕셔너리를 직접 해싱하지 않도록 캐싱 방식을 변경하여 에러를 잡았습니다.
def fetch_user_data():
    try:
        response = supabase.table('users').select('*').execute()
        creds = {'usernames': {}}
        for user in response.data:
            creds['usernames'][str(user['username'])] = {
                'name': str(user['name']),
                'password': str(user['password']),
                'role': str(user.get('role', 'viewer'))
            }
        return creds
    except:
        return {'usernames': {}}

# 인증 정보 로딩
if 'credentials' not in st.session_state:
    st.session_state.credentials = fetch_user_data()

# 인증기 초기화
authenticator = stauth.Authenticate(
    st.session_state.credentials, 
    'ceo_portal_v14', 
    'auth_key_v14', 
    cookie_expiry_days=30
)

# 로그인 화면
authenticator.login('main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    user_info = st.session_state.credentials['usernames'].get(username, {})
    user_role = user_info.get('role', 'viewer')
    real_name = user_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('시스템 로그아웃', 'sidebar')

    # ------------------------------------------
    # 👑 [ADMIN] 관리자 대시보드
    # ------------------------------------------
    if user_role == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2 = st.tabs(["📝 데이터 입력", "👥 고객 관리"])
        
        with t1:
            viewer_list = [u for u in st.session_state.credentials['usernames'] if st.session_state.credentials['usernames'][u].get('role') != 'admin']
            if not viewer_list: st.info("고객을 먼저 등록해 주세요.")
            else:
                selected_client = st.selectbox("리포트 대상", viewer_list, format_func=lambda x: f"{st.session_state.credentials['usernames'][x].get('name')} ({x})")
                with st.form("input_v14"):
                    c_name = st.text_input("업체명 (예: 불타는닭발)")
                    col1, col2 = st.columns(2)
                    score = col1.number_input("신용점수", 300, 1000, 850)
                    sales = col2.number_input("월 매출액(만원)", 0, 100000, 1500)
                    comment = st.text_area("공민준 센터장의 경영 제언")
                    if st.form_submit_button("리포트 발행"):
                        supabase.table('client_data').insert({
                            "client_id": selected_client, "company_name": c_name,
                            "credit_score": str(score), "monthly_sales": str(sales), "strategy_comment": comment
                        }).execute()
                        st.success("리포트가 성공적으로 발행되었습니다.")
                        st.rerun()

        with t2:
            st.subheader("신규 고객 등록")
            with st.form("reg_v14"):
                r_id = st.text_input("아이디")
                r_pw = st.text_input("비밀번호", type="password")
                r_name = st.text_input("고객 성함")
                if st.form_submit_button("계정 생성"):
                    hashed_pw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hashed_pw, "role": "viewer"}).execute()
                    st.session_state.credentials = fetch_user_data() # 데이터 갱신
                    st.success(f"{r_name} 대표님 등록 완료")
                    st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 프로 프리미엄 리포트
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
                latest = df.iloc[-1]

                # 상태 판별 로직
                status_color = "#27AE60" if latest['점수'] >= 840 else "#E74C3C"
                status_text = "정책자금 승인 권장" if latest['점수'] >= 840 else "신용 관리 집중 필요"

                # 1. 상단 헤더 디자인
                st.markdown(f"""
                    <div style="border-left: 10px solid {GOLD}; padding-left: 20px; margin-bottom: 40px;">
                        <p style="color: #95a5a6; font-size: 0.9rem; letter-spacing: 3px; margin: 0;">SNS7 BUSINESS ANALYTICS</p>
                        <h1 style="color: {NAVY}; font-size: 2.6rem; margin: 5px 0; font-weight: 700;">{real_name} 대표님 경영 리포트</h1>
                        <p style="color: {status_color}; font-size: 1.2rem; font-weight: 700; margin: 0;">● {status_text}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 2. 메트릭 카드
                m1, m2, m3 = st.columns(3)
                m1.markdown(f'<div class="metric-card"><p class="metric-label">분석 업체명</p><p class="metric-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                m2.markdown(f'<div class="metric-card"><p class="metric-label">현재 신용점수</p><p class="metric-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                m3.metric("최근 월 매출액", f"{latest['매출']:,} 만원") # Streamlit 기본 메트릭 혼용 (안정성)

                st.markdown("<br>", unsafe_allow_html=True)

                # 3. 차트 섹션
                c_col1, c_col2 = st.columns(2)
                
                with c_col1:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; font-size:1.1rem;">🛡️ 신용점수 분석 추이</p>', unsafe_allow_html=True)
                    chart_score = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=4, interpolate='monotone').encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[300, 1000]), title=None)
                    )
                    points = chart_score.mark_circle(size=120, color='#E74C3C')
                    labels = points.mark_text(dy=-20, fontSize=14, fontWeight='bold').encode(text='점수:Q')
                    st.altair_chart((chart_score + points + labels).properties(height=300), use_container_width=True)

                with c_col2:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; font-size:1.1rem;">💰 매출 성장 곡선 (단위: 억)</p>', unsafe_allow_html=True)
                    chart_sales = alt.Chart(df).mark_area(
                        line={'color': '#3498DB', 'width': 4},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('날짜:N', title=None),
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None)
                    )
                    st.altair_chart(chart_sales.properties(height=300), use_container_width=True)

                # 4. 공민준 센터장의 전략 제언
                st.markdown(f"""
                    <div style="background-color: {NAVY}; padding: 3rem; border-radius: 20px; margin-top: 3rem; position: relative;">
                        <h3 style="color: {GOLD}; font-size: 1.5rem; margin-bottom: 1.5rem; font-weight: 700;">💡 공민준 센터장의 경영 전략 제언</h3>
                        <p style="color: white; font-size: 1.15rem; line-height: 2; opacity: 0.95; white-space: pre-wrap;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 5. 하단 푸터
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<p style='color:#7f8c8d; font-size:0.9rem;'><b>공민준 센터장</b> | SNS7 비즈니스 센터<br>금융 자금 컨설팅 전문가</p>", unsafe_allow_html=True)
                f2.markdown(f"<p style='text-align:right; color:#bdc3c7; font-size:0.85rem;'>\"대표님의 성공이 곧 저희의 가치입니다.\"</p>", unsafe_allow_html=True)

            else: st.warning("아직 발행된 리포트가 없습니다. 관리자에게 문의하세요.")
        except Exception as e: st.error(f"데이터 로딩 오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보가 올바르지 않습니다.')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
