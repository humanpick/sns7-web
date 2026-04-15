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
    .stApp { background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    input, select, div[data-baseweb="select"] * { color: black !important; background-color: white !important; font-weight: bold !important; }
    
    /* 요약 수치 강조 */
    [data-testid="stMetricValue"] { font-size: 3.5rem !important; color: #1E3A8A !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; font-weight: bold !important; }
    
    /* 금리 인하 안내창 스타일 */
    .benefit-card {
        background-color: #DAA520; color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px; font-weight: bold; font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바 (기존과 동일하되 '대출 당시 점수' 입력 추가)
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    with st.expander("➕ 데이터 직접 넣기"):
        client_res = supabase.table("clients").select("*").execute()
        if client_res.data:
            names = {c['name']: c['id'] for c in client_res.data}
            target = st.selectbox("고객 선택", list(names.keys()))
            initial_score = st.number_input("대출 당시 점수", min_value=0, max_value=1000, value=700) # 신규 추가
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("현재 신용점수", min_value=0, max_value=1000, value=750)
            input_money = st.number_input("예상 절감액(원)", min_value=0, step=10000)
            
            if st.button("저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money,
                    "initial_score": initial_score # 창고에도 저장 (SQL에서 컬럼 추가 필요)
                }).execute()
                st.success("저장 완료!")
                st.rerun()

    st.divider()
    client_res_for_view = supabase.table("clients").select("*").execute()
    if client_res_for_view.data:
        view_names = {c['name']: c['id'] for c in client_res_for_view.data}
        current_user = st.selectbox("📊 리포트 조회", list(view_names.keys()))
    else: current_user = None

# [4] 메인 화면
if current_user:
    st.title(f"📊 {current_user} 경영 분석 리포트")
    
    try:
        target_id = view_names[current_user]
        res = supabase.table("financial_data").select("*").eq("client_id", target_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")
            latest = df.iloc[-1]
            
            # ⭐ [1] 금리 인하 혜택 로직 적용
            # (현재점수 >= 840) 이거나 (현재 - 대출당시 >= 70) 인 경우
            is_eligible = (latest['credit_score'] >= 840) or (latest['credit_score'] - latest.get('initial_score', 700) >= 70)
            
            if is_eligible:
                st.markdown(f'<div class="benefit-card">🎊 축하합니다! 금리 인하권 신청 대상입니다. (약 0.5%p 인하 가능)</div>', unsafe_allow_html=True)

            # [요약 카드]
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("현재 신용점수", f"{latest['credit_score']}점")
            col_b.metric("금리 인하 혜택", "0.5%p 적용 가능" if is_eligible else "관리 필요")
            col_c.metric("조회 기준월", f"{latest['date']}")
            
            st.write("---")

            # [메인 그래프 영역]
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 신용점수 추이 및 혜택 구간")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                fig.update_traces(textposition="top center", textfont_size=18, line=dict(width=5))
                # 혜택 기준선 (840점) 추가
                fig.add_hline(y=840, line_dash="dash", annotation_text="정상 회복 기준(840)", line_color="gold")
                fig.add_hline(y=700, line_dash="dot", annotation_text="신청 가능(700)", line_color="red")
                fig.update_layout(height=550, font=dict(size=15, weight="bold"))
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # ⭐ [2] 신용점수 대비 예상 정책자금 그래프
                st.subheader("🏦 점수별 예상 정책자금 한도")
                # 간단한 예측 로직 (점수별로 한도가 늘어나는 시각화)
                score_range = [600, 700, 800, 840, 900]
                fund_limits = [20000000, 50000000, 100000000, 150000000, 200000000]
                fund_df = pd.DataFrame({"점수": score_range, "한도": fund_limits})
                
                fig_fund = px.area(fund_df, x="점수", y="한도", color_discrete_sequence=["#1E3A8A"])
                # 현재 위치 표시
                fig_fund.add_vline(x=latest['credit_score'], line_color="red", annotation_text="현재 내 위치")
                fig_fund.update_layout(height=550, yaxis_tickformat=",.0f")
                st.plotly_chart(fig_fund, use_container_width=True)

            # ⭐ [3] 예상 절감액 그래프를 하단으로 이동
            st.divider()
            st.subheader("💰 월별 경영 비용 절감 성과 (단위: 원)")
            fig_saved = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
            fig_saved.update_traces(textfont_size=20, textfont_color="#1E3A8A", textposition="outside")
            fig_saved.update_layout(height=400, yaxis_tickformat=",.0f")
            fig_saved.update_xaxes(type='category')
            st.plotly_chart(fig_saved, use_container_width=True)

    except Exception as e:
        st.error(f"데이터를 불러오는 중입니다... (필요시 사이드바에서 데이터를 입력하세요)")

else:
    st.info("왼쪽 메뉴에서 리포트를 볼 사장님을 선택해주세요!")
