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

st.markdown("""
    <meta name="google" content="notranslate">
    <style>
    .block-container { padding-top: 0rem !important; margin-top: -50px !important; }
    header { visibility: hidden; height: 0px; }
    [data-testid="stElementActions"], .vega-actions { display: none !important; }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://pjpnaqyyzlkolnfvlpps.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcG5hcXl5emxrb2xuZnZscHBzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxOTEwNzgsImV4cCI6MjA5MTc2NzA3OH0.Y1kR473B-XdxnZZG3akAsp6kvGxTIL1S8IG7is8mgMM"


@st.cache_resource(show_spinner=False)
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"DB 연결 실패: {e}")
    st.stop()

# ==========================================
# 2. 데이터 통신 및 로그인
# ==========================================
def fetch_users():
    try:
        response = supabase.table('users').select('*').execute()
        credentials = {'usernames': {}}
        for user in response.data:
            credentials['usernames'][user['username']] = {
                'email': f"{user['username']}@ceo.com", 
                'name': user['name'], 'password': user['password'], 'role': user['role']
            }
        return credentials
    except: return {'usernames': {}}

credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state.get("authentication_status") == True:
    username = st.session_state["username"]
    
    try:
        user_res = supabase.table('users').select('name').eq('username', username).execute()
        real_name = user_res.data[0]['name'] if user_res.data else credentials['usernames'][username]['name']
    except: real_name = credentials['usernames'][username]['name']

    with st.sidebar:
        st.write(f"**{real_name}**님 반갑습니다.")
        authenticator.logout('로그아웃', 'sidebar')

    if credentials['usernames'][username]['role'] == 'admin':
        st.title("👑 관리자 대시보드")
    else:
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df.get('created_at', pd.Timestamp.now())).dt.tz_localize(None)
                df['날짜'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                df['점수'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)

                # 💡 [핵심] 매출을 10000으로 나누어 '억원' 단위로 변환 (엔진 오류 원천 차단)
                df['매출_억'] = df['매출'] / 10000.0

                df['점수_텍스트'] = df['점수'].astype(str)
                df['매출_텍스트'] = df['매출'].apply(lambda x: f"{x:,}")

                latest = df.iloc[-1]
                safe_score, safe_sales = int(latest['점수']), int(latest['매출'])
                
                bg_color = "#87CEEB" if safe_score > 839 else "#FFCCCC"
                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:10px; border-radius:10px; border:2px solid #333; text-align:center;">
                        <h3 style="color:black; margin:0 0 5px 0;">현재 상태: {"정책자금 기준(839) 충족" if safe_score > 839 else "정책자금 기준(839) 미달"}</h3>
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
                x_ax = alt.X('날짜:N', title='데이터 입력일', axis=alt.Axis(labelAngle=0, labelColor='black'))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    # 💡 [필수 복구] 실수로 지웠던 zero=False 를 다시 부활시켰습니다!
                    base = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[500, 999], zero=False, clamp=True), title='점수', axis=alt.Axis(labelColor='black'))
                    )
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    
                    chart1 = alt.layer(
                        rule, 
                        base.mark_line(color='#ff4b4b', size=3), 
                        base.mark_circle(size=150, color='#ff4b4b'), 
                        base.mark_text(dy=-20, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='점수_텍스트:N')
                    ).properties(height=350)
                    
                    st.altair_chart(chart1, use_container_width=True, theme=None)
                    st.caption("※ 회색 점선: 정책자금 권장 기준선 (839점)")

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    
                    # 💡 [혁신적 해결] 엔진을 뻗게 만드는 복잡한 수식을 삭제하고, Y축을 0.0 ~ 2.0(억)으로 깔끔하게 그립니다.
                    base_s = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('매출_억:Q', scale=alt.Scale(domain=[0, 2], clamp=True), title='매출 (단위: 억원)', 
                                axis=alt.Axis(
                                    values=[0, 0.5, 1.0, 1.5, 2.0], 
                                    format=".1f",  # 0.0, 0.5, 1.0 형태로 고정 출력
                                    labelColor='black'
                                ))
                    )
                    
                    chart2 = alt.layer(
                        base_s.mark_line(color='#0068c9', size=3), 
                        base_s.mark_circle(size=150, color='#0068c9'),
                        # 점 위에는 '1,300' 이라는 원래 텍스트가 정상적으로 표시됩니다.
                        base_s.mark_text(dy=-20, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='매출_텍스트:N')
                    ).properties(height=350)
                    
                    st.altair_chart(chart2, use_container_width=True, theme=None)
                    st.caption("※ 차트 범위: 0원 ~ 2억 원")

                st.divider()
                st.subheader("💡 공민준 센터장의 핵심 경영 제언")
                st.info(latest.get('strategy_comment', "제언 수립 중입니다."))
                
        except Exception as e:
             st.error(f"시스템 오류: {e}")

elif st.session_state.get("authentication_status") == False:
    st.error('아이디 또는 비밀번호를 확인해 주세요.')
elif st.session_state.get("authentication_status") == None:
    st.info('로그인해 주세요.')
