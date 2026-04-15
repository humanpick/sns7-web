import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 가게 인테리어 (더 크고 찐하게!)
st.set_page_config(page_title="SNS7 CEO 포털", layout="wide")
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #F8FAFC; }
    
    /* 사이드바 디자인 */
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    
    /* 사이드바 글자색 (하얀색으로 선명하게) */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { 
        color: white !important; 
        font-weight: bold !important;
    }
    
    /* 입력창 디자인 (하얀 바탕에 크고 찐한 검은 글씨) */
    input, select, div[data-baseweb="select"] * { 
        color: black !important; 
        background-color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    
    /* 골드 버튼 */
    .stButton>button { 
        background-color: #DAA520 !important; 
        color: white !important; 
        font-size: 1.2rem !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
    }
    
    /* 상단 요약 숫자(Metric) 아주 크게 만들기 */
    [data-testid="stMetricValue"] {
        font-size: 3rem !important;
        color: #1E3A8A !important;
        font-weight: 900 !important;
    }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바: 관리자 전용 메뉴
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    
    with st.expander("👤 새 사장님 이름 등록하기"):
        new_name = st.text_input("새 사장님 이름")
        if st.button("명단에 추가하기"):
            if new_name:
                supabase.table("clients").insert({"name": new_name}).execute()
                st.success("등록 완료!")
                st.rerun()

    with st.expander("➕ 데이터 직접 넣기"):
        client_res = supabase.table("clients").select("*").execute()
        if client_res.data:
            names = {c['name']: c['id'] for c in client_res.data}
            target = st.selectbox("누구 데이터를 넣을까요?", list(names.keys()))
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("신용점수", min_value=0, max_value=1000, value=750)
            input_money = st.number_input("절감액(원)", min_value=0, step=10000)
            
            if st.button("창고에 저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money
                }).execute()
                st.success("저장 완료!")
                st.rerun()

    st.divider()
    client_res_for_view = supabase.table("clients").select("*").execute()
    if client_res_for_view.data:
        view_names = {c['name']: c['id'] for c in client_res_for_view.data}
        current_user = st.selectbox("📊 리포트 볼 사장님 선택", list(view_names.keys()))
    else:
        current_user = None

# [4] 메인 화면: 그래프 보여주기
if current_user:
    st.title(f"📊 {current_user} 경영 리포트")
    st.write("---")

    try:
        target_id = view_names[current_user]
        res = supabase.table("financial_data").select("*").eq("client_id", target_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")
            
            # ⭐ [추가됨] 맨 위에 아주 큰 글씨로 핵심 요약 보여주기
            latest_data = df.iloc[-1] # 가장 최근 데이터 뽑기
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("최신 신용점수", f"{latest_data['credit_score']}점")
            col_b.metric("총 예상 절감액", f"{latest_data['saved_amount']:,}원")
            col_c.metric("최근 업데이트 월", f"{latest_data['date']}")
            st.write("---")

            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 신용점수 (정책자금 기준)")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                
                # 선 굵게, 숫자 크고 찐하게, 세로 높이(height) 500으로 늘리기
                fig.update_traces(textposition="top center", textfont_size=18, textfont_color="#1E3A8A", line=dict(width=5), marker=dict(size=12))
                fig.add_hline(y=800, line_dash="dot", annotation_text="안정(800)", line_color="green", annotation_font_size=14)
                fig.add_hline(y=700, line_dash="dot", annotation_text="커트라인(700)", line_color="red", annotation_font_size=14)
                
                # 날짜 심플하게, 전체 글자 크기 키우기
                fig.update_layout(height=500, font=dict(size=15, color="black", weight="bold"))
                fig.update_xaxes(type='category') # 날짜 중간값 안 나오게 딱 맞추기
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("💰 예상 절감액 (단위: 원)")
                fig2 = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
                
                # 숫자 크고 찐하게, 세로 높이 늘리기
                fig2.update_traces(textfont_size=18, textfont_color="#1E3A8A", textposition="outside")
                fig2.update_layout(height=500, yaxis_tickformat=",.0f", font=dict(size=15, color="black", weight="bold"))
                fig2.update_xaxes(type='category') # 날짜 깔끔하게
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("아직 데이터가 없습니다. 왼쪽 메뉴에서 점수를 먼저 넣어주세요!")

    except Exception as e:
        st.error(f"에러가 났어요: {e}")
else:
    st.title("📊 경영지원 실시간 리포트")
    st.info("왼쪽 메뉴에서 새로운 사장님을 등록해주세요!")
