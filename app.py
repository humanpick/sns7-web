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
    .stApp { background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { background-color: #DAA520 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바: 관리자 전용 메뉴
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    
    # ⭐ [새로 추가된 기능] 1. 새로운 사장님 이름부터 명단에 올리기
    with st.expander("👤 새 사장님 이름 등록하기"):
        st.write("처음 오신 사장님은 여기서 먼저 이름을 등록해주세요.")
        new_name = st.text_input("새 사장님 이름 (예: 김영희 대표님)")
        
        if st.button("명단에 추가하기"):
            if new_name: # 이름이 비어있지 않으면
                supabase.table("clients").insert({"name": new_name}).execute()
                st.success(f"'{new_name}'님이 창고 명단에 추가되었어요!")
                st.rerun() # 화면 새로고침
            else:
                st.warning("이름을 빈칸으로 둘 수 없어요!")

    # 2. 점수와 돈 데이터 넣기
    with st.expander("➕ 데이터 직접 넣기"):
        # 창고에서 사장님 명단 가져오기
        client_res = supabase.table("clients").select("*").execute()
        
        if not client_res.data:
            st.warning("등록된 사장님이 없습니다. 위에서 먼저 이름을 등록해주세요.")
        else:
            names = {c['name']: c['id'] for c in client_res.data}
            
            # 이제 명단에서 고를 수 있어요!
            target = st.selectbox("누구 데이터를 넣을까요?", list(names.keys()))
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("신용점수", min_value=0, max_value=1000, value=750)
            input_money = st.number_input("절감액(원)", min_value=0, step=1000)
            
            if st.button("창고에 저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money
                }).execute()
                st.success("데이터 저장 완료!")
                st.rerun()

    st.divider()
    
    # 3. 리포트 볼 사장님 선택하기
    client_res_for_view = supabase.table("clients").select("*").execute()
    if client_res_for_view.data:
        view_names = {c['name']: c['id'] for c in client_res_for_view.data}
        current_user = st.selectbox("📊 리포트 볼 사장님 선택", list(view_names.keys()))
    else:
        current_user = None

# [4] 메인 화면: 그래프 보여주기
if current_user:
    st.title(f"📊 {current_user} 경영 리포트")
    st.write(f"민준 지점장이 분석한 {current_user}의 실시간 데이터입니다.")

    try:
        target_id = view_names[current_user]
        res = supabase.table("financial_data").select("*").eq("client_id", target_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")

            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 신용점수 (정책자금 기준)")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                fig.add_hline(y=800, line_dash="dot", annotation_text="안정(800)", line_color="green")
                fig.add_hline(y=700, line_dash="dot", annotation_text="커트라인(700)", line_color="red")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("💰 예상 절감액 (단위: 원)")
                fig2 = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
                fig2.update_layout(yaxis_tickformat=",.0f")
                st.plotly_chart(fig2, use_container_width=True)

            # 상세 표 (금액 뒤에 '원' 붙이기)
            df_view = df[['date', 'credit_score', 'saved_amount']].copy()
            df_view['saved_amount'] = df_view['saved_amount'].apply(lambda x: f"{x:,}원")
            st.table(df_view)
        else:
            st.info("아직 데이터가 없습니다. 왼쪽 메뉴 [➕ 데이터 직접 넣기]에서 점수를 먼저 넣어주세요!")

    except Exception as e:
        st.error(f"에러가 났어요: {e}")
else:
    st.title("📊 경영지원 실시간 리포트")
    st.info("왼쪽 메뉴에서 새로운 사장님을 등록해주세요!")
