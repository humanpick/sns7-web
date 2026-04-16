import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt
import altair as alt

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# [핵심] 상단 공백 제거 및 그래프 부가 기능(아이콘) 완전 삭제 CSS
st.markdown("""
    <style>
    /* 1. 상단 여백 최소화 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -30px !important;
    }
    header {visibility: hidden; height: 0px;}
    
    /* 2. 그래프 우측 상단 '데이터 표시', '전체화면' 버튼 영구 제거 */
    [data-testid="stElementActions"] {
        display: none !important;
    }
    button[title="View fullscreen"] {
        display: none !important;
    }
    .stVegaLiteChart summary {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# [필수] 센터장님의 Supabase 정보를 입력하세요.
SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"DB 연결 실패: {e}")
    st.stop()

# ==========================================
# 2. 데이터베이스 통신 함수
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'email': f"{user['username']}@ceo.com", 
                'name': user['name'],
                'password': user['password'],
                'role': user['role']
            }
        return credentials
    except: return {'usernames': {}}

def update_password_in_db(username, hashed_password):
    supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()

# ==========================================
# 3. 로그인 및 인증 시스템 
# ==========================================
credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state["authentication_status"] == False:
    st.error('아이디 또는 비밀번호 오류입니다.')
elif st.session_state["authentication_status"] == None:
    st.info('아이디와 비밀번호를 입력해 주세요.')
    
elif st.session_state["authentication_status"] == True:
    username = st.session_state["username"]
    
    # [실시간 실명 동기화] 쿠키가 아닌 DB에서 이름을 즉시 가져옴
    try:
        user_res = supabase.table('users').select('name').eq('username', username).execute()
        real_name = user_res.data[0]['name'] if user_res.data else "대표님"
    except: real_name = "대표님"

    with st.sidebar:
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('로그아웃', 'sidebar')

    # ==========================================
    # 4-A. [관리자 모드]
    # ==========================================
    if credentials['usernames'][username]['role'] == 'admin':
        st.title("👑 관리자 대시보드")
        all_df = pd.DataFrame()
        try:
            res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if res.data:
                all_df = pd.DataFrame(res.data)
                st.dataframe(all_df, use_container_width=True)
        except: st.warning("데이터 로딩 중...")

        tab1, tab2 = st.tabs(["➕ 발행", "✏️ 수정"])
        with tab1:
            with st.form("new_form"):
                c_id = st.text_input("고객 ID"); c_name = st.text_input("성함 (실명)")
                c_score = st.number_input("신용점수", 0, 999, 850); c_sales = st.number_input("월매출(만원)", 0, 50000)
                c_comment = st.text_area("코멘트")
                if st.form_submit_button("발행"):
                    pw_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('users').upsert({'username': c_id, 'password': pw_hash, 'name': c_name, 'role': 'client'}).execute()
                    supabase.table('client_data').insert({'client_id': c_id, 'company_name': c_name, 'credit_score': c_score, 'monthly_sales': c_sales, 'strategy_comment': c_comment}).execute()
                    st.success("완료!"); st.rerun()

        with tab2:
            if not all_df.empty:
                edit_cid = st.selectbox("수정 고객", ["선택"] + all_df['client_id'].unique().tolist())
                if edit_cid != "선택":
                    edit_time = st.selectbox("수정 시간", all_df[all_df['client_id']==edit_cid]['created_at'].tolist())
                    target = all_df[all_df['created_at']==edit_time].iloc[0]
                    with st.form("edit_form"):
                        e_name = st.text_input("이름", target['company_name'])
                        e_score = st.number_input("점수", value=int(target['credit_score']))
                        e_sales = st.number_input("매출", value=int(target['monthly_sales']))
                        e_comment = st.text_area("제언", value=target['strategy_comment'])
                        if st.form_submit_button("수정"):
                            supabase.table('client_data').update({'company_name': e_name, 'credit_score': e_score, 'monthly_sales': e_sales, 'strategy_comment': e_comment}).eq('client_id', edit_cid).eq('created_at', edit_time).execute()
                            supabase.table('users').update({'name': e_name}).eq('username', edit_cid).execute()
                            st.success("수정 완료"); st.rerun()

    # ==========================================
    # 4-B. [고객 모드] 리포트 화면
    # ==========================================
    else:
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df = df.sort_values('created_at')
                df['date_label'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                latest = df.iloc[-1]
                safe_score = int(latest['credit_score'])
                safe_sales = int(latest['monthly_sales'])
                
                bg_color = "#87CEEB" if safe_score > 839 else "#FFCCCC"
                status_text = "정책자금 기준(839) 충족" if safe_score > 839 else "정책자금 기준(839) 미달"

                # 요약 박스 (높이 축소, 순서 변경)
                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:10px; border-radius:10px; border:2px solid #333; text-align:center;">
                        <h3 style="color:black; margin:0 0 5px 0;">현재 상태: {status_text}</h3>
                        <p style="color:black; font-size:16px; margin:0;">
                            <b>{real_name}</b> 대표님의 최신 신용점수는 <b>{safe_score}점</b> 입니다.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()

                m1, m2, m3 = st.columns(3)
                m1.metric("성함", real_name)
                m2.metric("최신 신용점수", f"{safe_score} 점")
                m3.metric("최신 월 매출액", f"{safe_sales:,} 만원")

                col1, col2 = st.columns(2)
                # X축 날짜 강제 고정
                x_ax = alt.X('date_label:N', title='데이터 입력 날짜', axis=alt.Axis(labelAngle=0))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base = alt.Chart(df).encode(x=x_ax, y=alt.Y('credit_score:Q', scale=alt.Scale(domain=[0, 999]), title='점수', axis=alt.Axis(labelColor='black')))
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    line = base.mark_line(color='#ff4b4b', size=3)
                    point = base.mark_circle(color='#ff4b4b', size=150)
                    text = base.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='credit_score:Q')
                    st.altair_chart(alt.layer(rule, line, point, text).properties(height=350), use_container_width=True)

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    # [해결] Y축 labelColor='black' 및 format=",.0f"로 숫자 선명하게 표기
                    base_s = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('monthly_sales:Q', scale=alt.Scale(domain=[0, 50000]), title='매출(만원)', 
                                axis=alt.Axis(values=[0,10000,20000,30000,40000,50000], format=",.0f", labelColor='black'))
                    )
                    line_s = base_s.mark_line(color='#0068c9', size=3)
                    point_s = base_s.mark_circle(color='#0068c9', size=150)
                    # [해결] 매출액 콤마(,) 포함 텍스트 강제 표기
                    text_s = base_s.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text=alt.Text('monthly_sales:Q', format=","))
                    st.altair_chart(alt.layer(line_s, point_s, text_s).properties(height=350), use_container_width=True)

                st.divider()
                st.subheader("💡 전문 경영 제언")
                st.info(latest.get('strategy_comment', "제언 수립 중입니다."))
                
        except Exception as e:
             st.error(f"데이터 연동 중...")
