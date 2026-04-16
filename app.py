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

# [마스터 CSS] 상단 공백 제거 및 아이콘 강제 삭제
st.markdown("""
    <style>
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -50px !important;
    }
    header {visibility: hidden; height: 0px;}
    footer {visibility: hidden;}
    
    /* 그래프 부가 기능 버튼 무조건 숨김 */
    [data-testid="stElementActions"], 
    .stElementActions,
    button[title="View fullscreen"],
    .vega-actions,
    summary,
    details {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
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

# ==========================================
# 3. 로그인 및 실명 동기화
# ==========================================
credentials = fetch_users()
authenticator = stauth.Authenticate(credentials, 'ceo_portal_cookie', 'signature_key', cookie_expiry_days=30)
authenticator.login('main')

if st.session_state["authentication_status"] == True:
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
        st.info("고객 데이터 관리 화면입니다.")
    else:
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                if 'created_at' not in df.columns: df['created_at'] = pd.Timestamp.now()
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df = df.sort_values('created_at')
                
                # 하단 데이터 입력일 텍스트
                df['date_label'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                # 수치 변환
                df['score_val'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['sales_val'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)
                
                latest = df.iloc[-1]
                safe_score = int(latest['score_val'])
                safe_sales = int(latest['sales_val'])
                
                bg_color = "#87CEEB" if safe_score > 839 else "#FFCCCC"
                status_text = "정책자금 기준(839) 충족" if safe_score > 839 else "정책자금 기준(839) 미달"

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
                
                # X축 (겹치더라도 날짜 강제 표기)
                x_ax = alt.X('date_label:N', title='데이터 입력일', axis=alt.Axis(labelAngle=0, labelColor='black', labelOverlap=False))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('score_val:Q', scale=alt.Scale(domain=[500, 999]), title='점수', axis=alt.Axis(labelColor='black'))
                    )
                    rule = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='y:Q')
                    line = base.mark_line(color='#ff4b4b', size=3)
                    point = base.mark_circle(color='#ff4b4b', size=150)
                    
                    # [핵심] clip=False를 넣어서 글씨가 잘리는 것을 원천 봉쇄
                    text = base.mark_text(
                        dy=-25, size=16, fontWeight='bold', color='black', clip=False
                    ).encode(text='score_val:Q')
                    
                    chart_score = alt.layer(rule, line, point, text).properties(height=350)
                    
                    # [핵심] theme=None 을 적용하여 스트림릿의 간섭을 완전히 차단!
                    st.altair_chart(chart_score, use_container_width=True, theme=None)
                    st.caption("※ 회색 점선: 정책자금 권장 기준선 (839점)")

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    base_s = alt.Chart(df).encode(
                        x=x_ax, 
                        y=alt.Y('sales_val:Q', scale=alt.Scale(domain=[0, 50000]), title='매출(만원)', 
                                axis=alt.Axis(values=[0, 10000, 20000, 30000, 40000, 50000], labelExpr="format(datum.value, ',')", labelColor='black'))
                    )
                    line_s = base_s.mark_line(color='#0068c9', size=3)
                    point_s = base_s.mark_circle(color='#0068c9', size=150)
                    
                    # [핵심] dy를 더 띄워서 바닥에 안 닿게 하고 clip=False 적용
                    text_s = base_s.mark_text(
                        dy=-25, size=16, fontWeight='bold', color='black', clip=False
                    ).encode(text=alt.Text('sales_val:Q', format=','))
                    
                    chart_sales = alt.layer(line_s, point_s, text_s).properties(height=350)
                    
                    # [핵심] theme=None 을 적용하여 스트림릿의 간섭을 완전히 차단!
                    st.altair_chart(chart_sales, use_container_width=True, theme=None)
                    st.caption("※ 차트 범위: 0원 ~ 5억 원 (50,000만 원)")

                st.divider()
                st.subheader("💡 공민준 센터장의 핵심 경영 제언")
                st.info(latest.get('strategy_comment', "제언 수립 중입니다."))
                
        except Exception as e:
             st.error(f"그래프 생성 중 오류 발생: {e}")

elif st.session_state["authentication_status"] == False:
    st.error('아이디/비밀번호가 일치하지 않습니다.')
elif st.session_state["authentication_status"] == None:
    st.info('로그인해 주세요.')
