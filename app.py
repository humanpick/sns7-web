import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 및 레이아웃 설정 (클린 UI 유지)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"

# 💡 상단 텍스트 노출 차단을 위한 CSS 주입
st.write(f"""
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

    .metric-box {{
        background-color: #FFFFFF !important;
        padding: 20px 25px !important;
        border-radius: 12px !important;
        border: 2px solid #D1D9E0 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        margin-bottom: 20px !important;
    }}
    .m-label {{ 
        font-size: 0.95rem !important; 
        color: #555 !important; 
        font-weight: 700 !important; 
        border-left: 4px solid {GOLD}; 
        padding-left: 10px; 
        margin-bottom: 10px;
    }}
    .m-value {{ 
        font-size: 1.8rem !important; 
        font-weight: 700 !important; 
        color: {NAVY} !important; 
    }}

    .stButton>button {{
        background-color: {GOLD} !important; color: {NAVY} !important;
        border: none !important; font-weight: 700 !important;
        padding: 0.6rem 2rem !important; border-radius: 6px !important;
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
# 2. 데이터 및 인증 로직 (캐싱 최적화)
# ==========================================
def fetch_creds():
    try:
        res = supabase.table('users').select('*').execute()
        c = {'usernames': {}}
        for u in res.data:
            c['usernames'][str(u['username'])] = {
                'name': str(u['name']), 'password': str(u['password']), 'role': str(u.get('role', 'viewer'))
            }
        return c
    except: return {'usernames': {}}

if 'creds' not in st.session_state:
    st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v17', 'key_v17', 30)
authenticator.login('main')

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
        t1, t2 = st.tabs(["📝 리포트 발행", "👥 고객 관리"])
        with t1:
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if not v_list: st.info("등록된 고객이 없습니다.")
            else:
                sel_id = st.selectbox("대상 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                with st.form("input_v17"):
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
                        st.success("발행 완료!")
                        st.rerun()

    # ------------------------------------------
    # 📈 [VIEWER] 프로페셔널 경영 리포트
    # ------------------------------------------
    else:
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            if res.data:
                df = pd.DataFrame(res.data)
                # 💡 [수정] 날짜를 '월-일' 형태로만 표기 (가독성 강화)
                df['날짜'] = pd.to_datetime(df['created_at']).dt.strftime('%m-%d')
                df['점수'] = pd.to_numeric(df['credit_score']).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales']).astype(int)
                df['매출_억'] = df['매출'] / 10000.0
                df['매출_표기'] = df['매출'].apply(lambda x: f"{x:,}만원") 
                latest = df.iloc[-1]

                # 타이틀 및 상태 배너
                st.markdown(f"<h3 style='color:{GOLD}; margin-bottom:0;'>SNS7 비즈니스 분석</h3>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color:{NAVY}; margin-top:0;'>{real_name} 대표님 경영 분석 리포트</h1>", unsafe_allow_html=True)
                status_msg = '신용 관리 집중 필요' if latest['점'수'] < 840 else '정책자금 승인 권장권'
                st.markdown(f"<p style='color:#E74C3C; font-weight:700;'>● {status_msg}</p>", unsafe_allow_html=True)

                st.write("")

                # 지표 카드
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-box"><p class="m-label">분석 업체명</p><p class="m-value">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-box"><p class="m-label">최신 신용점수</p><p class="m-value">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-box"><p class="m-label">최근 월 매출액</p><p class="m-value">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

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
                    # 💡 [수정] 매출 그래프 점 위에 금액 표기 추가
                    base_s = alt.Chart(df).encode(x=alt.X('날짜:N', title=None, axis=alt.Axis(labelAngle=0)))
                    area_s = base_s.mark_area(
                        line={'color': '#3498DB', 'width': 3},
                        color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3498DB', offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0)
                    ).encode(y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2]), title=None))
                    
                    points_s = base_s.mark_circle(size=120, color='#3498DB').encode(y='매출_억:Q')
                    # 💡 금액 텍스트 표기 레이어
                    labels_s = points_s.mark_text(dy=-20, fontSize=13, fontWeight='bold', color='#3498DB').encode(text='매출_표기:N')
                    
                    st.altair_chart((area_s + points_s + labels_s).properties(height=300), use_container_width=True)

                # 경영 전략 제시 박스
                st.write("")
                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid #D1D9E0; padding: 30px; border-radius: 12px;">
                        <h3 style="color: {NAVY}; margin-top: 0;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="color: #333; line-height: 1.8; white-space: pre-wrap; font-size: 1.05rem;">{latest['strategy_comment']}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.divider()
                st.caption("공민준 센터장 | SNS7 비즈니스 센터 | 금융 자금 컨설팅 전문가")

            else: st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"데이터 로딩 중 오류 발생: {e}")

elif st.session_state.get("authentication_status") is False: st.error('인증 정보가 올바르지 않습니다.')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
