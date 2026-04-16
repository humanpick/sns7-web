import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 및 레이아웃 설정 (가시성 및 정렬 강화)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BORDER_COLOR = "#E0E4E8"
BG_COLOR = "#F0F2F6"  # 배경색을 살짝 깔아서 화이트 카드와 구분

st.markdown(f"""
    <div class="notranslate" translate="no">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ 
        font-family: 'Pretendard', sans-serif !important; 
        background-color: {BG_COLOR} !important;
    }}
    
    header {{ visibility: hidden !important; height: 0px !important; }}
    .block-container {{ padding: 3rem 5rem !important; margin-top: -30px !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* 지표 카드 디자인: 배경과 확실히 구분되도록 테두리와 그림자 조정 */
    .metric-container {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1.5px solid {BORDER_COLOR};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: left;
        height: 100%;
    }}
    .metric-label {{ 
        font-size: 0.9rem; 
        color: #555; 
        margin-bottom: 0.8rem; 
        font-weight: 700;
        border-left: 3px solid {GOLD};
        padding-left: 8px;
    }}
    .metric-value {{ 
        font-size: 1.6rem; 
        font-weight: 700; 
        color: {NAVY}; 
        margin-top: 5px;
    }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2rem !important; border-radius: 5px !important;
    }}
    </style>
    </div>
""", unsafe_allow_html=True)

# ------------------------------------------
# [필수] Supabase 연결 설정
# ------------------------------------------
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ==========================================
# 2. 데이터 및 인증 시스템
# ==========================================
def fetch_users():
    try:
        res = supabase.table('users').select('*').execute()
        creds = {'usernames': {}}
        for u in res.data:
            creds['usernames'][str(u['username'])] = {
                'name': str(u['name']), 'password': str(u['password']), 'role': str(u.get('role', 'viewer'))
            }
        return creds
    except: return {'usernames': {}}

if 'credentials' not in st.session_state:
    st.session_state.credentials = fetch_users()

authenticator = stauth.Authenticate(st.session_state.credentials, 'ceo_portal_v15', 'key_v15', 30)
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

    if user_role == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2 = st.tabs(["📝 리포트 발행", "👥 고객 계정 관리"])
        with t1:
            viewer_list = [u for u in st.session_state.credentials['usernames'] if st.session_state.credentials['usernames'][u].get('role') != 'admin']
            if not viewer_list: st.info("고객을 등록해 주세요.")
            else:
                sel_client = st.selectbox("리포트 대상 선택", viewer_list, format_func=lambda x: f"{st.session_state.credentials['usernames'][x]['name']} ({x})")
                with st.form("input_v15"):
                    c_name = st.text_input("분석 업체명 (예: 불타는닭발)")
                    col1, col2 = st.columns(2)
                    score = col1.number_input("신용점수", 300, 1000, 850)
                    sales = col2.number_input("월 매출액(단위: 만원)", 0, 100000, 1300)
                    comment = st.text_area("공민준 센터장의 경영 전략 제시")
                    if st.form_submit_button("리포트 발행하기"):
                        supabase.table('client_data').insert({
                            "client_id": sel_client, "company_name": c_name,
                            "credit_score": str(score), "monthly_sales": str(sales), "strategy_comment": comment
                        }).execute()
                        st.success("리포트 전송 완료!")
                        st.rerun()
        with t2:
            with st.form("reg_v15"):
                r_id = st.text_input("신규 ID")
                r_pw = st.text_input("임시 PW", type="password")
                r_name = st.text_input("고객 성함")
                if st.form_submit_button("고객 계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.credentials = fetch_users()
                    st.success("계정이 생성되었습니다.")
                    st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 프로페셔널 경영 리포트
    # ------------------------------------------
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%y-%m-%d')
                df['점수'] = pd.to_numeric(df['credit_score']).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales']).astype(int)
                df['매출_억'] = df['매출'] / 10000.0
                # 차트 표기용 텍스트 생성
                df['매출_표기'] = df['매출'].apply(lambda x: f"{x:,}만")
                latest = df.iloc[-1]

                # 상단 헤더 섹션
                st.markdown(f"""
                    <div style="margin-bottom: 2rem;">
                        <span style="color: {GOLD}; font-weight: 700; letter-spacing: 1px;">SNS7 BUSINESS ANALYTICS</span>
                        <h1 style="color: {NAVY}; margin-top: 5px; font-weight: 700;">{real_name} 대표님 경영 분석 리포트</h1>
                    </div>
                """, unsafe_allow_html=True)

                # 💡 [개선] 지표 칸을 화이트 카드로 만들고 배경과 구분되도록 배치
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-container"><p class="metric-label">분석 업체명</p><p class="metric-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-container"><p class="metric-label">최신 신용점수</p><p class="metric-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-container"><p class="metric-label">최근 월 매출액</p><p class="metric-value">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

                st.write("")
                st.write("")

                # 차트 섹션
                c_col1, c_col2 = st.columns(2)
                
                with c_col1:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; font-size:1.1rem;">🛡️ 신용점수 분석 추이</p>', unsafe_allow_html=True)
                    chart_score = alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=3, interpolate='monotone').encode(
                        x=alt.X('날짜:N', title=None), y=alt.Y('점수:Q', scale=alt.Scale(domain=[300, 1000]), title=None)
                    )
                    points = chart_score.mark_circle(size=100, color='#E74C3C')
                    labels = points.mark_text(dy=-15, fontWeight='bold').encode(text='점수:Q')
                    st.altair_chart((chart_score + points + labels).properties(height=300), use_container_width=True)

                with c_col2:
                    st.markdown(f'<p style="font-weight:700; color:{NAVY}; font-size:1.1rem;">💰 매출 성장 곡선 (단위: 억)</p>', unsafe_allow_html=True)
                    # 💡 [수정] 매출 성장 곡선에 포인트와 숫자 표기 추가
                    area_sales = alt.Chart(df).mark_area(
                        line={'color': '#3498DB', 'width': 3},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(
                        x=alt.X('날짜:N', title=None), y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None)
                    )
                    points_s = alt.Chart(df).mark_circle(size=100, color='#3498DB').encode(
                        x='날짜:N', y='매출_억:Q'
                    )
                    labels_s = points_s.mark_text(dy=-15, fontWeight='bold', color='#3498DB').encode(text='매출_표기:N')
                    st.altair_chart((area_sales + points_s + labels_s).properties(height=300), use_container_width=True)

                # 💡 [수정] '제언' -> '제시'로 변경 및 디자인 정돈
                st.markdown(f"""
                    <div style="background-color: white; border: 1.5px solid {BORDER_COLOR}; padding: 2.5rem; border-radius: 15px; margin-top: 2rem;">
                        <h3 style="color: {NAVY}; font-size: 1.3rem; margin-bottom: 1.2rem; font-weight: 700;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="color: #333; font-size: 1.05rem; line-height: 1.8; white-space: pre-wrap;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("<br><br>", unsafe_allow_html=True)
                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<p style='color:#7f8c8d; font-size:0.9rem;'><b>공민준 센터장</b> | SNS7 비즈니스 센터<br>금융 자금 컨설팅 전문가</p>", unsafe_allow_html=True)
                f2.markdown(f"<p style='text-align:right; color:#bdc3c7; font-size:0.85rem;'>대표님의 비즈니스 성공을 위한 <br>가장 확실한 파트너가 되겠습니다.</p>", unsafe_allow_html=True)

            else: st.warning("발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"데이터 로딩 오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
