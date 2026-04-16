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

# [핵심] 차트 우측 상단 메뉴, 전체화면 버튼 영구 삭제
st.markdown("""
    <style>
    [data-testid="stElementActions"] {display: none !important;}
    button[title="View fullscreen"] {display: none !important;}
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
    st.error(f"데이터베이스 연결 실패: {e}")
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
    except Exception as e:
        return {'usernames': {}}

def update_password_in_db(username, hashed_password):
    supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()

# ==========================================
# 3. 로그인 및 인증 시스템 
# ==========================================
credentials = fetch_users()

authenticator = stauth.Authenticate(
    credentials,
    'ceo_portal_cookie', 
    'signature_key',     
    cookie_expiry_days=30 
)

authenticator.login('main')

if st.session_state["authentication_status"] == False:
    st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
elif st.session_state["authentication_status"] == None:
    st.info('발급받으신 아이디와 비밀번호를 입력해 주세요.')
    
elif st.session_state["authentication_status"] == True:
    
    username = st.session_state["username"]
    name = st.session_state["name"]
    user_role = credentials['usernames'][username]['role']
    
    # 쿠키 무시! DB에서 무조건 실명 가져오기
    try:
        user_res = supabase.table('users').select('name').eq('username', username).execute()
        real_name = user_res.data[0]['name'] if user_res.data else name
    except:
        real_name = name

    with st.sidebar:
        st.write(f"**{real_name}**님 반갑습니다.")
        st.divider()
        try:
            if authenticator.reset_password(username, 'sidebar'):
                new_hashed_pw = credentials['usernames'][username]['password']
                update_password_in_db(username, new_hashed_pw)
                st.success('비밀번호가 안전하게 변경되었습니다.')
        except Exception as e:
            st.error(f"비밀번호 변경 중 오류: {e}")
        st.divider()
        authenticator.logout('로그아웃', 'sidebar')

    # ==========================================
    # 4-A. [관리자 모드] 공민준 센터장 전용 
    # ==========================================
    if user_role == 'admin':
        st.title("👑 CEO 포털 통합 관리자 대시보드")
        
        all_df = pd.DataFrame()
        try:
            res = supabase.table('client_data').select('*').order('created_at', desc=True).execute()
            if res.data:
                all_df = pd.DataFrame(res.data)
                display_df = all_df.copy()
                if 'created_at' in display_df.columns:
                    display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("등록된 고객 데이터가 없습니다.")
        except:
            st.warning("⚠️ 'client_data' 테이블을 확인해 주세요.")
        
        st.divider()
        
        tab1, tab2 = st.tabs(["➕ 새 리포트 발행 (신규/추가)", "✏️ 기존 데이터 수정 (오타 수정)"])
        
        with tab1:
            st.subheader("신규 고객을 등록하거나, 기존 고객의 '새로운 날짜' 데이터를 추가합니다.")
            with st.form("new_data_form"):
                col1, col2 = st.columns(2)
                with col1:
                    c_id = st.text_input("고객 ID (접속용)", placeholder="예: client_kim")
                    c_name = st.text_input("대표자 성함 (실명)", placeholder="예: 김대중")
                with col2:
                    c_score = st.number_input("신용점수", min_value=0, max_value=999, value=850)
                    c_sales = st.number_input("월 매출 (만원 단위)", min_value=0, max_value=50000, step=100)
                c_comment = st.text_area("센터장님 전용 전략 코멘트")
                
                if st.form_submit_button("DB 저장 및 새 데이터 추가"):
                    if c_id and c_name:
                        try:
                            temp_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table('users').upsert({
                                'username': c_id, 'password': temp_hash, 'name': c_name, 'role': 'client'
                            }).execute()

                            supabase.table('client_data').insert({
                                'client_id': c_id, 'company_name': c_name, 
                                'credit_score': c_score, 'monthly_sales': c_sales, 'strategy_comment': c_comment
                            }).execute()

                            st.success(f"✅ [{c_name}] 대표님의 새 리포트가 발행되었습니다!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 실패: {e}")

        with tab2:
            st.subheader("잘못 입력된 기존 데이터를 찾아 수정합니다.")
            if not all_df.empty:
                unique_cids = all_df['client_id'].unique().tolist()
                edit_cid = st.selectbox("1. 수정할 고객 ID 선택", ["선택하세요"] + unique_cids)
                
                if edit_cid != "선택하세요":
                    client_df = all_df[all_df['client_id'] == edit_cid].sort_values('created_at', ascending=False)
                    date_options = client_df['created_at'].tolist()
                    display_dates = [str(x)[:19].replace('T', ' ') for x in date_options]
                    
                    selected_display = st.selectbox("2. 수정할 데이터의 입력 시간 선택", ["선택하세요"] + display_dates)
                    
                    if selected_display != "선택하세요":
                        target_idx = display_dates.index(selected_display)
                        target_record = client_df.iloc[target_idx]
                        
                        with st.form("edit_existing_form"):
                            st.write(f"**{target_record.get('company_name', '')}** 대표님의 데이터를 수정합니다.")
                            col1, col2 = st.columns(2)
                            with col1:
                                e_name = st.text_input("대표자 성함 (실명 수정)", value=target_record.get('company_name', ''))
                            with col2:
                                e_score = st.number_input("신용점수 수정", min_value=0, max_value=999, value=int(target_record.get('credit_score', 0)))
                                e_sales = st.number_input("월 매출 수정 (만원)", min_value=0, max_value=50000, step=100, value=int(target_record.get('monthly_sales', 0)))
                            e_comment = st.text_area("전략 코멘트 수정", value=target_record.get('strategy_comment', ''))
                            
                            if st.form_submit_button("✅ 수정한 내용으로 덮어쓰기"):
                                try:
                                    supabase.table('client_data').update({
                                        'company_name': e_name,
                                        'credit_score': e_score,
                                        'monthly_sales': e_sales,
                                        'strategy_comment': e_comment
                                    }).eq('client_id', edit_cid).eq('created_at', target_record['created_at']).execute()
                                    
                                    supabase.table('users').update({
                                        'name': e_name
                                    }).eq('username', edit_cid).execute()
                                    
                                    st.success("데이터 수정이 완벽하게 반영되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"수정 중 오류 발생: {e}")
            else:
                st.info("수정할 고객 데이터가 존재하지 않습니다.")

    # ==========================================
    # 4-B. [고객 모드] 업체 대표님 전용
    # ==========================================
    else:
        st.title(f"📈 {real_name} 대표님 맞춤형 경영 리포트")
        
        try:
            res = supabase.table('client_data').select('*').eq('client_id', username).execute()
            
            if res.data:
                df = pd.DataFrame(res.data)
                
                if 'created_at' not in df.columns:
                    df['created_at'] = '2026-01-01T00:00:00'
                
                df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
                df = df.sort_values('created_at')

                df['date_label'] = df['created_at'].dt.strftime('%Y-%m-%d')
                df['score_num'] = pd.to_numeric(df['credit_score'], errors='coerce').fillna(0).astype(int)
                df['sales_num'] = pd.to_numeric(df['monthly_sales'], errors='coerce').fillna(0).astype(int)
                
                df['score_str'] = df['score_num'].astype(str)
                df['sales_str'] = df['sales_num'].apply(lambda x: f"{x:,}")
                
                latest_data = df.iloc[-1]
                safe_score = int(latest_data['score_num'])
                safe_sales = int(latest_data['sales_num'])
                
                bg_color = "#87CEEB" if safe_score > 839 else "#FFCCCC"
                status_text = "정책자금 기준(839) 충족" if safe_score > 839 else "정책자금 기준(839) 미달"

                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:10px; border-radius:10px; border: 2px solid #333; text-align:center;">
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
                
                x_axis = alt.X('date_label:N', title='데이터 입력 날짜', axis=alt.Axis(labelAngle=0, values=df['date_label'].unique().tolist()))

                with col1:
                    st.subheader("🛡️ 신용점수 분석 추이")
                    base_score = alt.Chart(df).encode(
                        x=x_axis,
                        y=alt.Y('score_num:Q', scale=alt.Scale(domain=[0, 999]), title='신용점수 (0~999점)', axis=alt.Axis(values=[0, 200, 400, 600, 800, 999]))
                    )
                    rule_score = alt.Chart(pd.DataFrame({'y': [839]})).mark_rule(strokeDash=[5, 5], color='gray').encode(y='y:Q')
                    line_score = base_score.mark_line(color='#ff4b4b', size=3)
                    point_score = base_score.mark_circle(color='#ff4b4b', size=150)
                    text_score = base_score.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='score_str:N')
                    
                    st.altair_chart(alt.layer(rule_score, line_score, point_score, text_score).properties(height=350), use_container_width=True)
                    st.caption("※ 회색 점선: 정책자금 권장 기준선 (839점)")

                with col2:
                    st.subheader("💰 월 매출 성장 추이")
                    
                    # 💡 [핵심 해결] 에러를 일으키던 format 속성을 빼고, 엔진이 절대 거부할 수 없는 자바스크립트 수식(labelExpr)으로 콤마(,)를 강제했습니다!
                    base_sales = alt.Chart(df).encode(
                        x=x_axis,
                        y=alt.Y('sales_num:Q', scale=alt.Scale(domain=[0, 50000]), title='월 매출액 (만원)', 
                                axis=alt.Axis(values=[0, 10000, 20000, 30000, 40000, 50000], labelExpr="format(datum.value, ',')"))
                    )
                    line_sales = base_sales.mark_line(color='#0068c9', size=3)
                    point_sales = base_sales.mark_circle(color='#0068c9', size=150)
                    text_sales = base_sales.mark_text(dy=-25, fontSize=15, fontWeight='bold', color='black', clip=False).encode(text='sales_str:N')
                    
                    st.altair_chart(alt.layer(line_sales, point_sales, text_sales).properties(height=350), use_container_width=True)
                    st.caption("※ 차트 범위: 0원 ~ 5억 원 (50,000만 원)")

                st.divider()
                st.subheader("💡 공민준 센터장의 핵심 경영 제언")
                st.info(latest_data.get('strategy_comment', "세부 전략 수립 중입니다."))
                
            else:
                st.warning("아직 발행된 리포트가 없습니다.")
        except Exception as e:
             st.error(f"시스템 에러 발생: {e}")
