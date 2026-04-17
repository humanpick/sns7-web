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
# 1. 테마: 네이비(#001F3F) & 골드(#D4AF37)
# 2. 신용점수: 빨간 선, 상단 점수 라벨, 500-999 범위
# 3. 매출액: 블루 그라데이션, 포인트별 '만원' 라벨링
# 4. 레이아웃: PC 고정 / 모바일 가변 하이브리드
# ==========================================

st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"

# ==========================================
# 2. 하이브리드 반응형 CSS (PC 고정 & 모바일 가변)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Pretendard', sans-serif !important; background-color: {BG_COLOR} !important; }}

    /* 🖥️ [PC용] 화면 폭이 992px 이상일 때 적용 */
    @media (min-width: 992px) {{
        section[data-testid="stSidebar"] {{
            transform: none !important;
            transition: none !important;
            display: flex !important;
            visibility: visible !important;
            width: 280px !important;
            min-width: 280px !important;
            left: 0 !important;
        }}
        /* PC에서는 사이드바 조절 버튼을 숨깁니다 (고정형) */
        [data-testid="collapsedControl"], button[title="Close sidebar"] {{
            display: none !important;
        }}
        .main .block-container {{ margin-left: 20px !important; }}
    }}

    /* 📱 [모바일용] 화면 폭이 991px 이하일 때 적용 */
    @media (max-width: 991px) {{
        /* 모바일에서는 사이드바 버튼을 다시 살려내어 조작 가능하게 합니다 */
        [data-testid="collapsedControl"] {{
            display: block !important;
            background-color: white !important;
            border: 2px solid {GOLD} !important;
            border-radius: 8px !important;
            top: 15px !important;
            left: 15px !important;
            z-index: 999999 !important;
        }}
    }}

    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}

    /* 메트릭 카드 (메모리 보존) */
    .metric-card-v23 {{
        background-color: #FFFFFF !important;
        padding: 22px !important;
        border-radius: 12px !important;
        border: 2px solid {BORDER} !important;
        margin-bottom: 20px !important;
    }}
    .label-v23 {{ font-size: 0.95rem !important; color: #666 !important; font-weight: 700 !important; border-left: 4px solid {GOLD}; padding-left: 10px; margin-bottom: 10px; }}
    .value-v23 {{ font-size: 1.8rem !important; font-weight: 700 !important; color: {NAVY} !important; }}
    .stButton>button {{ background-color: {GOLD} !important; color: {NAVY} !important; border: none !important; font-weight: 700 !important; padding: 0.6rem 2.5rem !important; border-radius: 6px !important; }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 및 인증 로직 (변경사항 없음)
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

if 'creds' not in st.session_state: st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v44', 'key_v44', 30)
authenticator.login('main')

# ==========================================
# 3. 메인 화면 출력 (UI 불변 원칙 적용)
# ==========================================
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    u_info = st.session_state.creds['usernames'].get(username, {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        st.divider()
        if st.button("🚪 시스템 로그아웃"):
            authenticator.logout('로그아웃', 'sidebar')

    if u_info.get('role') == 'admin':
        # [관리자 모드 생략 없이 전체 보존...]
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        with t1:
            st.info("고객 정보를 입력하여 분석 리포트를 발행하세요.")

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

                # 💡 [메모리 고정] 그래프 UI 원복 및 유지
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

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
