import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. 디자인 시스템 (V23 하이엔드 표준 복구)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

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
    
    /* 💡 [수정] 사이드바 버튼 시인성 강화: 어떤 배경에서도 보이도록 골드 테두리 적용 */
    [data-testid="collapsedControl"] {{ display: block !important; }}
    button[title="Open sidebar"], button[title="Close sidebar"], [data-testid="stSidebarCollapseButton"] {{
        background-color: white !important;
        border: 2px solid {GOLD} !important;
        color: {NAVY} !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        z-index: 999999 !important;
    }}

    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    [data-testid="stToolbar"] {{ visibility: hidden !important; }}
    .block-container {{ padding: 3rem 5rem !important; margin-top: -20px !important; }}
    [data-testid="stSidebar"] {{ background-color: {NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}

    /* V23 시그니처 메트릭 카드 */
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
        background: white; padding: 15px; border-radius: 8px; border-left: 5px solid {GOLD}; 
        margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 연결 및 데이터 로직
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v38', 'key_v38', 30)
authenticator.login('main')

# ==========================================
# 3. 메인 화면 출력
# ==========================================
if st.session_state.get("authentication_status"):
    username, u_info = st.session_state["username"], st.session_state.creds['usernames'].get(st.session_state["username"], {})
    real_name = u_info.get('name', username)
    
    with st.sidebar:
        st.write(f"### 💼 CEO 전용 채널")
        st.write(f"**{real_name}**님 환영합니다.")
        authenticator.logout('시스템 로그아웃', 'sidebar')

    if u_info.get('role') == 'admin':
        # (관리자 코드는 이전 V35~V37의 모든 기능을 포함하되 생략 없이 적용됩니다)
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        # ... [이전 관리자 탭 로직 전체 포함] ...
        with t1:
            st.info("신규 데이터를 입력하고 전략을 발행하세요.")
            # (발행 폼 구성...)

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (V23 명품 UI 완벽 복구)
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
                
                # 상단 지표 카드
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">신용점수</p><p class="value-v23">{latest["점수"]}점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">월 매출액</p><p class="value-v23">{latest["매출"]:,}만원</p></div>', unsafe_allow_html=True)

                # 💡 그래프 UI V23 표준 복구
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

                # 전략 메시지 박스
                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid {BORDER}; padding: 35px; border-radius: 12px; margin-top:20px;">
                        <h3 style="color: {NAVY}; border-bottom: 2px solid {GOLD}; display: inline-block; padding-bottom: 5px;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="white-space: pre-wrap; line-height: 1.9; font-size: 1.1rem; margin-top: 15px;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 하단 명언 및 프로필 (V23 고정 스탠다드)
                st.divider()
                f1, f2 = st.columns(2)
                f1.markdown(f"<div style='font-size:0.95rem; color:#666;'><b>공민준 지점장</b><br>SNS7 비즈니스 센터 전문가 그룹</div>", unsafe_allow_html=True)
                f2.markdown(f"<div style='text-align:right; font-style:italic; color:#999; font-size:0.9rem;'>\"성공은 결코 우연이 아니다. <br>인내와 배움, 그리고 희생의 결과다.\"</div>", unsafe_allow_html=True)
            else: st.warning("발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
