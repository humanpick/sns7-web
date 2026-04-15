import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 가게 인테리어 (숫자는 더 거대하게, 색상은 선명하게!)
st.set_page_config(page_title="SNS7 CEO 포털", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    input, select, div[data-baseweb="select"] * { color: black !important; background-color: white !important; font-weight: bold !important; font-size: 1.1rem !important; }
    
    /* 🚨 메인 숫자(Metric) 초대형 사이즈 & 컬러 튜닝 */
    [data-testid="stMetricValue"] { 
        font-size: 4rem !important; /* 엄청나게 큰 사이즈 */
        color: #DAA520 !important; /* 번쩍이는 찐한 골드 */
        font-weight: 900 !important; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1); /* 살짝 그림자 줘서 입체감 */
    }
    [data-testid="stMetricLabel"] { 
        font-size: 1.5rem !important; /* 제목도 큼지막하게 */
        color: #1E3A8A !important; /* 제목은 찐한 네이비 */
        font-weight: 900 !important; 
    }
    
    /* 금리 인하 안내창 스타일 */
    .benefit-card {
        background-color: #DAA520; color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px; font-weight: bold; font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바 
with st.sidebar:
    st.title("⚙️ 관리자 메뉴")
    with st.expander("➕ 데이터 직접 넣기"):
        client_res = supabase.table("clients").select("*").execute()
        if client_res.data:
            names = {c['name']: c['id'] for c in client_res.data}
            target = st.selectbox("고객 선택", list(names.keys()))
            initial_score = st.number_input("대출 당시 점수", min_value=0, max_value=1000, value=700)
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("현재 신용점수", min_value=0, max_value=1000, value=750)
            input_money = st.number_input("예상 절감액(원)", min_value=0, step=10000)
            
            if st.button("저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money,
                    "initial_score": initial_score
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
            current_score = latest['credit_score']
            
            # 금리 인하권 로직
            is_eligible = (current_score >= 840) or (current_score - latest.get('initial_score', 700) >= 70)
            
            if is_eligible:
                st.markdown(f'<div class="benefit-card">🎊 축하합니다! 금리 인하 신청 가능 (약 0.5%p 인하)</div>', unsafe_allow_html=True)

            # [상단 요약 카드]
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("현재 신용점수", f"{current_score}점")
            col_b.metric("금리 인하 혜택", "신청 가능!" if is_eligible else "관리 필요")
            col_c.metric("조회 기준월", f"{latest['date']}")
            
            st.write("---")

            # [메인 그래프 영역]
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 신용점수 추이 및 혜택 구간")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                
                # 숫자 폰트 크기 대폭 상향 (22) 및 굵게
                fig.update_traces(textposition="top center", textfont_size=24, textfont_color="#1E3A8A", line=dict(width=5), marker=dict(size=14))
                fig.add_hline(y=840, line_dash="dash", annotation_text="정상 회복 기준(840)", line_color="gold")
                fig.add_hline(y=700, line_dash="dot", annotation_text="신청 가능(700)", line_color="red")
                fig.update_layout(height=500, font=dict(size=16, weight="bold"))
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # ⭐ [직관성 끝판왕] 점수 구간별 한도 막대그래프
                st.subheader("🏦 점수 구간별 예상 정책자금 한도")
                
                # 구간 정의
                tiers = ["700점 미만", "700~799점", "800~839점", "840점 이상"]
                limits = [20000000, 50000000, 100000000, 150000000]
                labels = ["2천만 원", "최대 5천만 원", "최대 1억 원", "1.5억 원 이상"]
                
                # 내 점수가 어디에 속하는지 찾기
                if current_score < 700: my_tier = "700점 미만"
                elif current_score < 800: my_tier = "700~799점"
                elif current_score < 840: my_tier = "800~839점"
                else: my_tier = "840점 이상"
                
                fund_df = pd.DataFrame({"구간": tiers, "한도": limits, "설명": labels})
                # 내 구간은 찐한 골드, 나머지는 흐린 회색으로 칠하기
                fund_df["색상"] = fund_df["구간"].apply(lambda x: "#DAA520" if x == my_tier else "#D1D5DB")
                
                fig_fund = px.bar(fund_df, x="구간", y="한도", text="설명", color="색상", color_discrete_map="identity")
                
                # 막대 위 글자 아주 크게
                fig_fund.update_traces(textposition="outside", textfont_size=20, textfont_color="#1E3A8A")
                # 지저분한 Y축 숫자 숨기고 깔끔하게
                fig_fund.update_layout(height=500, showlegend=False, font=dict(size=16, weight="bold"))
                fig_fund.update_yaxes(visible=False, showgrid=False)
                st.plotly_chart(fig_fund, use_container_width=True)

            st.divider()
            st.subheader("💰 월별 경영 비용 절감 성과 (단위: 원)")
            fig_saved = px.bar(df, x="date", y="saved_amount", text_auto=',.0f', color_discrete_sequence=["#DAA520"])
            fig_saved.update_traces(textfont_size=22, textfont_color="#1E3A8A", textposition="outside")
            fig_saved.update_layout(height=400, yaxis_tickformat=",.0f", font=dict(size=16, weight="bold"))
            fig_saved.update_xaxes(type='category')
            st.plotly_chart(fig_saved, use_container_width=True)

    except Exception as e:
        st.error(f"데이터 로딩 중 오류: {e}")

else:
    st.info("왼쪽 메뉴에서 리포트를 볼 사장님을 선택해주세요!")
