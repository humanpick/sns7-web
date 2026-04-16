import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import pandas as pd
import bcrypt

# 💡 [핵심] 완벽한 그래프를 위해 Plotly 엔진을 사용합니다.
# 만약 에러가 난다면 터미널에 `pip install plotly` 를 딱 한 번만 쳐주세요!
try:
    import plotly.graph_objects as go
except ImportError:
    st.error("🚨 그래프 엔진(Plotly)이 설치되어 있지 않습니다. 터미널(명령 프롬프트)에 아래 명령어를 입력해주세요!\n\n`pip install plotly`")
    st.stop()

# ==========================================
# 1. 시스템 설정 및 Supabase 연동
# ==========================================
st.set_page_config(page_title="SNS7 CEO 포털", page_icon="💼", layout="wide")

# [마스터 CSS] 상단 공백 극한 축소 (Plotly는 툴바가 자체적으로 숨겨지므로 CSS가 가볍습니다)
st.markdown("""
    <meta name="google" content="notranslate">
    <style>
    .block-container { padding-top: 0rem !important; margin-top: -50px !important; }
    header { visibility: hidden; height: 0px; }
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
        st.info("고객 데이터 관리 화면입니다.")
    else:
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).order('created_at').execute()
            
            if res.data:
                df = pd.DataFrame(res.data)
                df['created_at'] = pd.to_datetime(df.get('created_at', pd.Timestamp.now())).dt.tz_localize(None)
                df['date_label'] = df['created_at'].dt.strftime('%Y-%m-%d')
                
                df['점수'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['매출'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)

                # 숫자 포맷팅을 미리 생성 (Plotly 적용용)
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

                # ==========================================
                # 📊 [왼쪽] 신용점수 분석 추이 (Plotly)
                # ==========================================
                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    fig1 = go.Figure()
                    
                    # 꺾은선 및 점, 숫자 강제 표기 (절대 사라지지 않음)
                    fig1.add_trace(go.Scatter(
                        x=df['date_label'], y=df['점수'],
                        mode='lines+markers+text',
                        text=df['점수_텍스트'],
                        textposition='top center', # 점 위에 선명하게 배치
                        line=dict(color='#ff4b4b', width=3),
                        marker=dict(size=12, color='#ff4b4b'),
                        textfont=dict(size=16, color='black')
                    ))
                    
                    # 정책자금 기준선 (839점)
                    fig1.add_hline(y=839, line_dash="dash", line_color="gray")
                    
                    # 레이아웃 강제 고정 (500~999점)
                    fig1.update_layout(
                        yaxis=dict(range=[500, 999], title='점수', tickfont=dict(color='black')),
                        xaxis=dict(title='데이터 입력일', tickfont=dict(color='black')),
                        height=350,
                        margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='white', paper_bgcolor='white'
                    )
                    fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
                    fig1.update_xaxes(showgrid=False)
                    
                    # config={'displayModeBar': False} 를 통해 우측 상단 툴바를 영구 박멸
                    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
                    st.caption("※ 회색 점선: 정책자금 권장 기준선 (839점)")

                # ==========================================
                # 📊 [오른쪽] 월 매출 성장 추이 (Plotly)
                # ==========================================
                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Scatter(
                        x=df['date_label'], y=df['매출'],
                        mode='lines+markers+text',
                        text=df['매출_텍스트'],
                        textposition='top center',
                        line=dict(color='#0068c9', width=3),
                        marker=dict(size=12, color='#0068c9'),
                        textfont=dict(size=16, color='black')
                    ))
                    
                    # 레이아웃 강제 고정 및 텍스트 매핑 (0원 ~ 2억)
                    fig2.update_layout(
                        yaxis=dict(
                            range=[0, 20000],
                            title='매출(단위: 만원)',
                            # 💡 요청하신 금액을 강제로 축에 때려 박습니다. 에러 없음 보장!
                            tickvals=[0, 1000, 2000, 3000, 5000, 10000, 20000],
                            ticktext=['0원', '1천만원', '2천만원', '3천만원', '5천만원', '1억원', '2억원'],
                            tickfont=dict(color='black')
                        ),
                        xaxis=dict(title='데이터 입력일', tickfont=dict(color='black')),
                        height=350,
                        margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='white', paper_bgcolor='white'
                    )
                    fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E5E5')
                    fig2.update_xaxes(showgrid=False)
                    
                    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
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
