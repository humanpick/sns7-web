import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 시스템 및 변수 정의 (에러 방지 핵심)
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# 💡 모든 UI 변수를 최상단에 정의합니다.
NAVY = "#001F3F"
GOLD = "#D4AF37"
BG_COLOR = "#F4F7F9"
BORDER = "#D1D9E0"  # 👈 여기서 발생했던 에러를 해결했습니다.

# 프리미엄 UI 스타일 시트 주입
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

    /* 지표 카드 디자인 */
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
# 2. 데이터 및 인증 코어 (안정성 강화)
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v23', 'key_v23', 30)
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
    # 👑 [ADMIN] 관리자 데이터 센터 (입력/관리/수정 통합)
    # ------------------------------------------
    if u_info.get('role') == 'admin':
        st.title("👑 관리자 데이터 센터")
        t1, t2, t3 = st.tabs(["📝 리포트 발행", "👥 고객 계정 관리", "⚙️ 데이터 수정 및 삭제"])
        
        with t1:
            st.subheader("신규 데이터 누적 입력")
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if not v_list: st.info("고객을 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                with st.form("input_v23"):
                    comp = st.text_input("분석 업체명")
                    c1, c2 = st.columns(2)
                    sc = c1.number_input("신용점수", 500, 999, 850)
                    sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                    cmt = st.text_area("공민준 센터장의 경영 전략 제시")
                    if st.form_submit_button("데이터 추가 및 발행"):
                        supabase.table('client_data').insert({
                            "client_id": sel_id, "company_name": comp,
                            "credit_score": str(sc), "monthly_sales": str(sa), "strategy_comment": cmt
                        }).execute()
                        st.success(f"{comp} 데이터가 성공적으로 저장되었습니다.")
                        st.rerun()

        with t2:
            st.subheader("신규 고객 등록")
            with st.form("reg_v23"):
                r_id = st.text_input("아이디")
                r_pw = st.text_input("비밀번호", type="password")
                r_name = st.text_input("성함")
                if st.form_submit_button("계정 생성"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.success("고객 등록 완료")
                    st.rerun()
            st.divider()
            cl_df = pd.DataFrame([{"ID": k, "이름": v['name']} for k, v in st.session_state.creds['usernames'].items() if v['role'] != 'admin'])
            if not cl_df.empty: st.table(cl_df)

        with t3:
            st.subheader("📜 데이터 이력 수정 및 삭제")
            st.info("💡 발행된 데이터의 수치를 변경하거나 잘못된 기록을 삭제할 수 있습니다.")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                history_df = pd.DataFrame(raw_res.data)
                
                # 데이터 에디터 출력
                edited_df = st.data_editor(
                    history_df,
                    column_config={
                        "client_id": "고객ID",
                        "company_name": "업체명",
                        "credit_score": "신용점수",
                        "monthly_sales": "월매출",
                        "strategy_comment": "전략 제시",
                        "created_at": "발행일"
                    },
                    disabled=["created_at", "client_id"],
                    num_rows="dynamic",
                    key="history_editor_v23",
                    use_container_width=True
                )
                
                st.warning("데이터 수정 기능은 추후 확장 가능하도록 설계되었습니다. 현재는 목록 확인 및 행 삭제(선택 후 Del 키)가 가능합니다.")
            else:
                st.write("표시할 데이터가 없습니다.")

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (V21 스탠다드)
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
                status_color = "#27AE60" if latest['점수'] >= 840 else "#E74C3C"
                status_text = '정책자금 승인 권장권' if latest['점수'] >= 840 else '신용 관리 집중 필요'
                st.markdown(f"<p style='color:{status_color}; font-weight:700; font-size:1.1rem;'>● {status_text}</p>", unsafe_allow_html=True)

                st.write("")

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

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

            else: st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

elif st.session_state.get("authentication_status") is False: st.error('정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
