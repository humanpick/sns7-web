import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠 (수정 금지)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 가게 인테리어 (네이비 & 골드)
st.set_page_config(page_title="SNS7 CEO 포털", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; } /* 밝은 배경 */
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; } /* 네이비 사이드바 */
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { background-color: #DAA520 !important; color: white !important; } /* 골드 버튼 */
</style>
""", unsafe_allow_html=True)

# [3] 사이드바: 데이터 넣기 & 사장님 고르기
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    
    # --- 새로운 데이터 입력하는 곳 ---
    with st.expander("➕ 데이터 직접 넣기"):
        # 창고에서 사장님 명단 가져오기
        client_res = supabase.table("clients").select("*").execute()
        names = {c['name']: c['id'] for c in client_res.data}
        
        target = st.selectbox("누구 데이터를 넣을까요?", list(names.keys()))
        input_date = st.date_input("기준 날짜")
        input_score = st.number_input("신용점수", min_value=0, max_value=1000, value=750)
        input_money = st.number_input("절감액(원)", min_value=0, step=1000)
        
        if st.button("창고에 저장하기"):
            supabase.table("financial_data").insert({
                "client_id": names[target],
                "date": input_date.strftime("%Y-%m"), # '2026-04' 처럼 저장해요
                "credit_score": input_score,
                "saved_amount": input_money
            }).execute()
            st.success("저장 완료!")
            st.rerun()

    st.divider()
    # --- 조회할 사장님 선택 ---
    current_user = st.selectbox("📊 리포트 볼 사장님 선택", list(names.keys()))

# [4] 메인 화면: 그래프 보여주기
st.title(f"📊 {current_user} 경영 리포트")
st.write(f"민준 지점장이 분석한 {current_user}의 실시간 데이터입니다.")

try:
    # 선택한 사장님의 데이터만 창고에서 가져오기
    target_id = names[current_user]
    res = supabase.table("financial_data").select("*").eq("client_id", target_id).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df = df.sort_values("date")

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 신용점수 (정책자금 기준)")
            fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
            # 정책자금 기준선 그어주기
            fig.add_hline(y=800, line_dash="dot", annotation_text="안정(800)", line_color="green")
            fig.add_hline(y=700, line_dash="dot", annotation_text="커트라인(700)", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("💰 예상 절감액 (단위: 원)")
            # 돈 뒤에 '원' 붙이고 콤마 찍기
            fig2 = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
            fig2.update_layout(yaxis_tickformat=",.0f")
            st.plotly_chart(fig2, use_container_width=True)

        # 상세 표 (금액 뒤에 '원' 붙이기)
        df_view = df[['date', 'credit_score', 'saved_amount']].copy()
        df_view['saved_amount'] = df_view['saved_amount'].apply(lambda x: f"{x:,}원")
        st.table(df_view)
    else:
        st.info("아직 데이터가 없습니다. 왼쪽에서 데이터를 먼저 넣어주세요!")

except Exception as e:
    st.error(f"에러가 났어요: {e}")
