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

# [핵심] 차트 메뉴, 전체화면 버튼, 상단 공백을 '물리적'으로 지워버리는 CSS
st.markdown("""
    <style>
    /* 상단 여백 제거 */
    .block-container { padding-top: 0rem !important; margin-top: -50px !important; }
    header { visibility: hidden; height: 0px; }
    
    /* 그래프 우측 상단 지분거리는 아이콘들(데이터 표시, 전체화면) 무조건 삭제 */
    div[data-testid="stElementActions"], 
    .stElementActions, 
    button[title="View fullscreen"], 
    details, summary {
        display: none !important;
        visibility: hidden !important;
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
    st.error(f"DB 연결 실패. 주소나 키를 확인해 주세요: {e}")
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

# ==========================================
# 3. 로그인 시스템
# ==========================================
credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state["authentication_status"] == True:
    username = st.session_state["username"]
    
    # DB 실시간 이름 동기화
    try:
        user_res = supabase.table('users').select('name').eq('username', username).execute()
        real_name = user_res.data[0]['name'] if user_res.data else credentials['usernames'][username]['name']
    except: real_name = credentials['usernames'][username]['name']

    with st.sidebar:
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('로그아웃', 'sidebar')

    # [분기] 관리자 vs 고객
    if credentials['usernames'][username]['role'] == 'admin':
        st.title("👑 센터장님 관리자 모드")
        st.info("데이터를 등록하거나 수정하는 화면입니다.")
    else:
        # --- 고객 리포트 화면 ---
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            # 1. 데이터 가져오기
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            
            if res.data:
                df = pd.DataFrame(res.data)
                
                # 2. 데이터 정제 (에러 방어용)
                if 'created_at' not in df.columns: df['created_at'] = pd.Timestamp.now()
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df = df.sort_values('created_at')
                df['날짜'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                # 숫자로 변환
                df['점수'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)
                
                latest = df.iloc[-1]
                safe_score = int(latest['점수'])
                safe_sales = int(latest['매출'])
                
                bg_color = "#87CEEB" if safe_score > 839 else "#FFCCCC"
                status_text = "정책자금 기준(839) 충족" if safe_score > 839 else "정책자금 기준(839) 미달"

                # 상단 박스 (순서: 상태 위 / 안내 아래)
                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:10px; border-radius:10px; border:2px solid #333; text-align:center;">
                        <h3 style="color:black; margin:0 0 5px 0;">현재 상태: {status_text}</h3>
                        <p style="color:black; font-size:16px; margin:0;">
                            <b>{real_name}</b> 대표님의 최신 신용점수는 <b>{safe_score}점</b> 입니다.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()

                # 지표
                m1, m2, m3 = st.columns(3)
                m1.metric("성함", real_name)
                m2.metric("최신 신용점수", f"{safe_score} 점")
                m3.metric("최신 월 매출액", f"{safe_sales:,} 만원")

                col1, col2 = st.columns(2)
                x_axis = alt.X('날짜:N', title='데이터 입력 날짜', axis=alt.Axis(labelAngle=0))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base = alt.Chart(df).encode(x=x_axis, y=alt.Y('점수:Q', scale=alt.Scale(domain=[0, 999]), title='점수'))
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    line = base.mark_line(color='#ff4b4b', size=3)
                    point = base.mark_circle(color='#ff4b4b', size=150)
                    text = base.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='점수:Q')
                    # 에러를 일으키던 configure_view 삭제하고 순수 레이어만 사용
                    st.altair_chart(alt.layer(rule, line, point, text).properties(height=350), use_container_width=True)

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    # Y축 축 숫자 검정색으로 강제 고정
                    base_s = alt.Chart(df).encode(
                        x=x_axis, 
                        y=alt.Y('매출:Q', scale=alt.Scale(domain=[0, 50000]), title='매출(만원)', 
                                axis=alt.Axis(values=[0,10000,20000,30000,40000,50000], format=",.0f", labelColor='black'))
                    )
                    line_s = base_s.mark_line(color='#0068c9', size=3)
                    point_s = base_s.mark_circle(color='#0068c9', size=150)
                    text_s = base_s.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text=alt.Text('매출:Q', format=","))
                    st.altair_chart(alt.layer(line_s, point_s, text_s).properties(height=350), use_container_width=True)

                st.divider()
                st.subheader("💡 공민준 센터장의 핵심 경영 제언")
                st.info(latest.get('strategy_comment', "제언 수립 중입니다."))
                
            else:
                st.warning("아직 발행된 리포트가 없습니다.")
                
        except Exception as e:
             # 진짜 에러 원인을 화면에 표시합니다.
             st.error(f"시스템 오류 발생: {e}")

elif st.session_state["authentication_status"] == False:
    st.error('아이디/비밀번호를 확인해 주세요.')
elif st.session_state["authentication_status"] == None:
    st.info('로그인해 주세요.')
