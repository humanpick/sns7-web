import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 명품 카드형 인테리어 설정
st.set_page_config(page_title="SNS7 재무관리 리포트", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F1F5F9; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    input, select, div[data-baseweb="select"] * { color: black !important; background-color: white !important; font-weight: bold !important; }
    
    .graph-card {
        background-color: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0; margin-bottom: 25px;
    }

    [data-testid="stMetricValue"] { font-size: 3.5rem !important; color: #DAA520 !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.3rem !important; color: #1E3A8A !important; font-weight: bold !important; }

    .benefit-card {
        background-color: #DAA520; color: white; padding: 25px; border-radius: 20px;
        text-align: center; margin-bottom: 30px; font-weight: bold; font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바 관리자 메뉴
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    with st.expander("➕ 데이터 직접 넣기"):
        client_res = supabase.table("clients").select("*").execute()
        if client_res.data:
            names = {c['name']: c['id'] for c in client_res.data}
            target = st.selectbox("고객 선택", list(names.keys()))
            init_score = st.number_input("대출 당시 점수", min_value=0, max_value=1000, value=700)
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("현재 신용점수", min_value=0, max_value=1000, value=750)
            # ⭐ 매출 입력칸 추가
            input_sales = st.number_input("월평균 매출(원)", min_value=0, step=100000)
            input_money = st.number_input("예상 절감액(원)", min_value=0, step=10000)
            
            if st.button("저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money,
                    "initial_score": init_score,
                    "monthly_sales": input_sales # 창고에 저장
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
    st.title(f"📊 {current_user} 재무관리 분석 리포트")
    
    try:
        target_id = view_names[current_user]
        res = supabase.table("financial_data").select("*").eq("client_id", target_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")
            latest = df.iloc[-1]
            
            # 금리 인하권 로직
            is_eligible = (latest['credit_score'] >= 840) or (latest['credit_score'] - latest.get('initial_score', 700) >= 70)
            
            if is_eligible:
                st.markdown(f'<div class="benefit-card">🎊 금리 인하권 신청 대상입니다! (약 0.5%p 인하 가능)</div>', unsafe_allow_html=True)

            # [상단 요약 섹션]
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("현재 신용점수", f"{latest['credit_score']}점")
            # ⭐ 최근 매출 표시
            col_b.metric("최근 월 매출", f"{latest.get('monthly_sales', 0):,}원")
            col_c.metric("총 예상 절감액", f"{latest['saved_amount']:,}원")
            
            st.write("---")

            # [중단 섹션: 신용점수 vs 정책자금 한도]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("📈 신용점수 변화 추이")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                fig.update_traces(textposition="top center", textfont_size=20, line=dict(width=5))
                fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("🏦 점수별 정책자금 한도")
                # (기존 한도 로직 동일)
                tiers = ["700점 미만", "700~799점", "800~839점", "840점 이상"]
                limits = [20, 50, 100, 150]
                my_score = latest['credit_score']
                my_tier = tiers[0] if my_score < 700 else tiers[1] if my_score < 800 else tiers[2] if my_score < 840 else tiers[3]
                
                fund_df = pd.DataFrame({"구간": tiers, "한도": limits})
                fund_df["색상"] = fund_df["구간"].apply(lambda x: "#DAA520" if x == my_tier else "#E2E8F0")
                fig_fund = px.bar(fund_df, x="구간", y="한도", text=fund_df["한도"].apply(lambda x: f"{x}천만"), color="색상", color_discrete_map="identity")
                fig_fund.update_traces(textposition="outside", textfont_size=18)
                fig_fund.update_layout(height=450, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig_fund.update_yaxes(visible=False)
                st.plotly_chart(fig_fund, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # [하단 섹션: 월 매출 vs 절감 성과]
            col3, col4 = st.columns(2)
            with col3:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("📊 월별 매출 성장 추이")
                fig_sales = px.bar(df, x="date", y="monthly_sales", text_auto=',.0f', color_discrete_sequence=["#1E3A8A"])
                fig_sales.update_traces(textfont_size=18, textfont_color="white", textposition="inside")
                fig_sales.update_layout(height=400, yaxis_tickformat=",.0f", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig_sales.update_xaxes(type='category')
                st.plotly_chart(fig_sales, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col4:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("💰 월별 경영 비용 절감액")
                fig_saved = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
                fig_saved.update_traces(textfont_size=18, textfont_color="black", textposition="outside")
                fig_saved.update_layout(height=400, yaxis_tickformat=",.0f", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig_saved.update_xaxes(type='category')
                st.plotly_chart(fig_saved, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.info("데이터를 분석하는 중입니다... 사이드바에서 매출을 포함한 데이터를 입력해 보세요!")

else:
    st.info("왼쪽 메뉴에서 리포트를 조회할 사장님을 선택해주세요.")
