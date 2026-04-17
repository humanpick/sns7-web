import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt

# ==========================================
# 1. 디자인 시스템 및 변수 (절대 고정)
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

    /* 지표 카드: SNS7 마스터 스탠다드 */
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

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v26', 'key_v26', 30)
authenticator.login('main')

# ------------------------------------------
# 💡 [AI 엔진] 전략 자동 생성 로직
# ------------------------------------------
def generate_strategy(score, sales):
    if score >= 900: sc_text = "최상위권 신용도를 유지 중입니다."
    elif score >= 840: sc_text = "정책자금 승인 권장권으로 매우 안정적입니다."
    elif score >= 750: sc_text = "보통 수준의 신용도이나, 자금 조달을 위해 상향 관리가 필요합니다."
    else: sc_text = "현재 신용도 관리가 시급한 단계입니다. 연체 관리 및 카드 이용 패턴 점검이 필요합니다."

    if sales >= 5000: sl_text = "규모의 경제를 실현하는 단계로, 시설 자금 확보를 통한 확장이 필요합니다."
    elif sales >= 1500: sl_text = "성장기로 접어들었습니다. 고정비 최적화와 운전 자금 확보가 핵심입니다."
    else: sl_text = "기초 체력을 다지는 시기입니다. 초기 정책자금 및 보증 한도 증액을 우선 검토해야 합니다."

    if score >= 840 and sales >= 1500:
        conclusion = "현시점은 저금리 정책자금을 최대한 확보하여 사업 규모를 키우기에 최적의 타이밍입니다."
    elif score < 840 and sales >= 1500:
        conclusion = "매출은 양호하나 신용도가 발목을 잡을 수 있습니다. 신용 관리에 집중하여 대출 금리를 낮추는 것이 급선무입니다."
    else:
        conclusion = "소상공인 지원 사업과 기초 미소금융 자금을 활용하여 리스크를 분산하며 성장을 도모해야 합니다."

    return f"{sc_text}\n\n{sl_text}\n\n💡 결론: {conclusion}\n\n추가적인 상세 실행 방안은 다음 대면 컨설팅에서 논의하겠습니다."

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
        t1, t2, t3 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리"])
        
        with t1:
            st.subheader("신규 데이터 누적 입력 및 전략 발행")
            v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']
            if not v_list: st.info("고객을 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: f"{st.session_state.creds['usernames'][x]['name']} ({x})")
                
                # 💡 [해결] 빈칸 저장 방지를 위한 세션 키 초기화
                if 'strat_text' not in st.session_state:
                    st.session_state.strat_text = ""
                
                with st.form("input_v26"):
                    comp = st.text_input("분석 업체명")
                    c1, c2 = st.columns(2)
                    sc = c1.number_input("신용점수", 500, 999, 850)
                    sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                    
                    st.write("---")
                    st.write("💡 **[순서 안내]** 아래 **1번** 버튼으로 전략을 생성한 후, **2번** 버튼으로 최종 저장하세요.")
                    
                    # session_state와 안전하게 동기화되는 텍스트 박스
                    cmt = st.text_area("공민준 센터장의 경영 전략 제시", key="strat_text", height=150)
                    
                    # 💡 [해결] 버튼의 역할을 확실하게 분리
                    col_btn1, col_btn2 = st.columns(2)
                    auto_btn = col_btn1.form_submit_button("💡 1. 전략 자동 생성 (AI 비서)")
                    save_btn = col_btn2.form_submit_button("💾 2. 최종 저장 및 리포트 발행")

                # 폼 바깥에서 저장 및 생성 로직 처리 (빈칸 버그 원천 차단)
                if auto_btn:
                    st.session_state.strat_text = generate_strategy(sc, sa)
                    st.rerun()

                if save_btn:
                    final_cmt = st.session_state.strat_text # 현재 텍스트 박스의 값을 정확히 가져옵니다.
                    supabase.table('client_data').insert({
                        "client_id": sel_id, "company_name": comp,
                        "credit_score": str(sc), "monthly_sales": str(sa), "strategy_comment": final_cmt
                    }).execute()
                    st.session_state.strat_text = "" # 전송 후 텍스트 박스 초기화
                    st.success(f"{comp} 리포트가 성공적으로 저장 및 발행되었습니다!")
                    st.rerun()

        # [T2: 계정 관리, T3: 이력 관리 로직]
        with t2:
            with st.form("reg_v26"):
                r_id = st.text_input("아이디")
                r_pw = st.text_input("비밀번호", type="password")
                r_name = st.text_input("성함")
                if st.form_submit_button("등록 완료"):
                    hpw = bcrypt.hashpw(r_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').insert({"username": r_id, "name": r_name, "password": hpw, "role": "viewer"}).execute()
                    st.session_state.creds = fetch_creds()
                    st.success("계정이 생성되었습니다.")
                    st.rerun()
            st.divider()
            cl_df = pd.DataFrame([{"ID": k, "이름": v['name']} for k, v in st.session_state.creds['usernames'].items() if v['role'] != 'admin'])
            if not cl_df.empty: st.table(cl_df)

        with t3:
            st.info("💡 발행된 데이터의 수치를 변경하거나 삭제할 수 있습니다.")
            raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if raw_res.data:
                edited_df = st.data_editor(
                    pd.DataFrame(raw_res.data),
                    column_config={"client_id":"ID", "company_name":"업체", "credit_score":"점수", "monthly_sales":"매출", "strategy_comment":"전략", "created_at":"발행일"},
                    disabled=["created_at", "client_id"], num_rows="dynamic", use_container_width=True
                )

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (민준님 지정 UI 100% 보존)
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

                # 💡 [방어 코드] 만약 과거의 빈칸 데이터가 불러와진 경우 안내 메시지 출력
                strat_text = latest.get('strategy_comment', '')
                if pd.isna(strat_text) or str(strat_text).strip() == "":
                    strat_text = "센터장의 맞춤형 경영 전략을 분석 및 작성 중입니다."

                st.write("")
                st.markdown(f"""
                    <div style="background-color: white; border: 2px solid {BORDER}; padding: 35px; border-radius: 12px;">
                        <h3 style="color: {NAVY}; margin-top: 0; border-bottom: 2px solid {GOLD}; display: inline-block; padding-bottom: 5px;">💡 공민준 센터장의 경영 전략 제시</h3>
                        <p style="color: #333; line-height: 1.9; white-space: pre-wrap; font-size: 1.1rem; margin-top: 20px;">{strat_text}</p>
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
