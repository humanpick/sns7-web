import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import altair as alt
import bcrypt
from datetime import datetime, time

# ==========================================
# 1. 디자인 시스템 및 변수 (V23 절대 고정 스탠다드)
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
    
    .sch-item {{ 
        background: white; padding: 15px; border-radius: 8px; 
        border-left: 5px solid {GOLD}; margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Supabase 연결 설정
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

def get_client_display_map():
    display_map = {}
    try:
        res = supabase.table('client_data').select('client_id, company_name').order('created_at', desc=True).execute()
        temp_map = {item['client_id']: item['company_name'] for item in res.data}
        for username, info in st.session_state.creds['usernames'].items():
            if info['role'] != 'admin':
                company = temp_map.get(username, "업체 정보 없음")
                display_map[username] = f"{info['name']} | {company}"
    except: pass
    return display_map

if 'creds' not in st.session_state:
    st.session_state.creds = fetch_creds()

authenticator = stauth.Authenticate(st.session_state.creds, 'ceo_portal_v33', 'key_v33', 30)
authenticator.login('main')

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
        t1, t2, t3, t4 = st.tabs(["📝 리포트 발행", "👥 고객 관리", "⚙️ 이력 관리", "📅 스케줄 관리"])
        
        client_map = get_client_display_map()
        v_list = [u for u in st.session_state.creds['usernames'] if st.session_state.creds['usernames'][u].get('role') != 'admin']

        with t1:
            st.subheader("신규 데이터 누적 입력 및 전략 발행")
            if st.session_state.get('save_success_msg'):
                st.success(st.session_state.save_success_msg)
                st.session_state.save_success_msg = "" 

            if not v_list: 
                st.info("고객을 먼저 등록해 주세요.")
            else:
                sel_id = st.selectbox("대상 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                comp = st.text_input("분석 업체명 (최신화)")
                c1, c2 = st.columns(2)
                sc = c1.number_input("신용점수", 500, 999, 850)
                sa = c2.number_input("월 매출액(만원)", 0, 100000, 1300)
                
                st.write("---")
                if st.button("💡 1. 전략 자동 생성 (AI 비서)"):
                    st.session_state.strat_text = generate_strategy(sc, sa)
                    st.rerun()
                
                if 'strat_text' not in st.session_state:
                    st.session_state.strat_text = ""
                
                cmt = st.text_area("공민준 센터장의 경영 전략 제시", key="strat_text", height=150)
                
                if st.button("💾 2. 최종 저장 및 리포트 발행"):
                    if not comp:
                        st.warning("분석 업체명을 입력해 주세요.")
                    else:
                        try:
                            supabase.table('client_data').insert({
                                "client_id": sel_id, 
                                "company_name": comp,
                                "credit_score": sc,   
                                "monthly_sales": sa,  
                                "strategy_comment": cmt
                            }).execute()
                            st.session_state.save_success_msg = f"{comp} 리포트가 성공적으로 발행되었습니다!"
                            if 'strat_text' in st.session_state: del st.session_state.strat_text
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 오류: {e}")

        with t2:
            st.subheader("👥 고객 계정 관리 및 비밀번호 수정")
            if v_list:
                with st.expander("🔐 특정 고객 비밀번호 강제 재설정", expanded=False):
                    target_u = st.selectbox("수정할 고객 선택", v_list, format_func=lambda x: client_map.get(x, x))
                    new_pw = st.text_input("새로운 비밀번호 입력", type="password", key="new_pw_input")
                    if st.button("비밀번호 즉시 변경"):
                        if new_pw:
                            hpw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table('users').update({"password": hpw}).eq('username', target_u).execute()
                            st.session_state.creds = fetch_creds()
                            st.success(f"비밀번호가 성공적으로 변경되었습니다.")
                        else: st.warning("새 비밀번호를 입력해 주세요.")

            st.divider()
            st.subheader("🆕 신규 고객 등록")
            with st.form("reg_v33"):
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
            st.subheader("📋 전체 고객 명단 및 암호 상태")
            cl_data = [{"아이디": k, "이름": v['name'], "저장된 암호(해시)": v['password']} for k, v in st.session_state.creds['usernames'].items() if v['role'] != 'admin']
            if cl_data:
                st.dataframe(pd.DataFrame(cl_data), use_container_width=True)

        with t3:
            st.info("💡 에디터에서 행을 지우거나 수정한 뒤, 반드시 아래의 **[DB 영구 반영]** 버튼을 눌러야 실제 서버에 적용됩니다.")
            try:
                raw_res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
                if raw_res.data:
                    history_df = pd.DataFrame(raw_res.data)
                    edited_df = st.data_editor(
                        history_df,
                        column_config={"id": None, "client_id": "고객ID", "company_name": "업체", "credit_score": "점수", "monthly_sales": "매출", "strategy_comment": "전략", "created_at": "발행일"},
                        disabled=["created_at", "client_id"], num_rows="dynamic", use_container_width=True
                    )
                    if st.button("🗑️ 변경/삭제사항 DB에 영구 반영하기"):
                        original_times = set(history_df['created_at'].tolist())
                        current_times = set(edited_df['created_at'].tolist())
                        deleted_times = original_times - current_times
                        
                        for d_time in deleted_times:
                            supabase.table('client_data').delete().eq('created_at', d_time).execute()
                        
                        for idx, row in edited_df.iterrows():
                            orig_row = history_df[history_df['created_at'] == row['created_at']].iloc[0]
                            if (str(row['company_name']) != str(orig_row['company_name']) or str(row['credit_score']) != str(orig_row['credit_score']) or str(row['monthly_sales']) != str(orig_row['monthly_sales']) or str(row['strategy_comment']) != str(orig_row['strategy_comment'])):
                                supabase.table('client_data').update({"company_name": row['company_name'], "credit_score": int(row['credit_score']), "monthly_sales": int(row['monthly_sales']), "strategy_comment": str(row['strategy_comment'])}).eq('created_at', row['created_at']).execute()
                        st.success("데이터베이스 원본 동기화 완료!")
                        st.rerun()
            except Exception as e: st.error(f"이력 관리 시스템 오류: {e}")

        with t4:
            st.subheader("📅 센터장님 고객 관리 스케줄")
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_date = st.date_input("날짜 선택", datetime.now())
                st.write("---")
                with st.container():
                    sch_client_id = st.selectbox("관련 고객 선택", ["일반 일정"] + v_list, format_func=lambda x: client_map.get(x, x))
                    sch_time = st.time_input("시간", time(10, 0))
                    sch_content = st.text_area("일정 내용")
                    if st.button("📅 일정 등록"):
                        display_name = client_map.get(sch_client_id, sch_client_id) if sch_client_id != "일반 일정" else "일반 일정"
                        supabase.table('schedules').insert({"client_id": display_name, "schedule_date": str(sel_date), "schedule_time": str(sch_time), "content": sch_content}).execute()
                        st.rerun()
            with c2:
                st.write(f"### 3. {sel_date} 상세 스케줄")
                sch_res = supabase.table('schedules').select('*').eq('schedule_date', str(sel_date)).order('schedule_time').execute()
                if sch_res.data:
                    for item in sch_res.data:
                        st.markdown(f"""
                            <div class="sch-item">
                                <span style="color:{GOLD}; font-weight:bold;">[{item['schedule_time'][:5]}]</span> 
                                <span style="color:{NAVY}; font-weight:bold;">{item['client_id']}</span><br>
                                <div style="margin-top:5px; color:#333;">{item['content']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"삭제 #{item['id']}", key=f"del_{item['id']}"):
                            supabase.table('schedules').delete().eq('id', item['id']).execute()
                            st.rerun()
                else: st.write("해당 날짜에 등록된 일정이 없습니다.")

    # ------------------------------------------
    # 📈 [VIEWER] 하이엔드 경영 리포트 (민준님 스탠다드 100% 완전 복구)
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
                with m1: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">분석 업체명</p><p class="value-v23">{latest["company_name"]}</p></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최신 신용점수</p><p class="value-v23">{latest["점수"]} 점</p></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card-v23"><p class="label-v23">최근 월 매출액</p><p class="value-v23">{latest["매출"]:,} 만원</p></div>', unsafe_allow_html=True)

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

elif st.session_state.get("authentication_status") is False: st.error('로그인 정보 불일치')
elif st.session_state.get("authentication_status") is None: st.info('계정 정보를 입력하여 접속해 주세요.')
