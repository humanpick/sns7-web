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
            target = st.selectbox("고객 선택", list(names.keys()))
            init_score = st.number_input("대출 당시 점수", min_value=0, max_value=1000, value=700)
            input_date = st.date_input("기준 날짜")
            input_score = st.number_input("현재 신용점수", min_value=0, max_value=1000, value=750)
            input_sales = st.number_input("월평균 매출(원)", min_value=0, step=100000)
            input_money = st.number_input("예상 절감액(원)", min_value=0, step=10000)
            
            if st.button("저장하기"):
                supabase.table("financial_data").insert({
                    "client_id": names[target],
                    "date": input_date.strftime("%Y-%m"),
                    "credit_score": input_score,
                    "saved_amount": input_money,
                    "initial_score": init_score,
                    "monthly_sales": input_sales
                }).execute()
                st.success("저장 완료!")
                st.rerun()

    st.divider()
    client_res_for_view = supabase.table("clients").select("*").execute()
    if client_res_for_view.data:
        view_names = {c['name']: c['id'] for c in client_res_for_view.data}
        current_user = st.selectbox("📊 리포트 조회", list(view_names.keys()))
        selected_id = view_names[current_user] # 선택된 사장님 고유번호 기억
    else: 
        current_user = None
        selected_id = None

# [4] 메인 화면
if current_user and selected_id:
    # 🚨 여기서 탭(방)을 확실하게 2개로 나눕니다!
    tab1, tab2 = st.tabs(["📈 분석 리포트 확인", "🛠️ 데이터 수정/삭제"])

    with tab1:
        st.title(f"📊 {current_user} 재무관리 분석 리포트")
        try:
            res = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                df = df.sort_values("date")
                latest = df.iloc[-1]
                
                is_eligible = (latest['credit_score'] >= 840) or (latest['credit_score'] - latest.get('initial_score', 700) >= 70)
                if is_eligible:
                    st.markdown(f'<div class="benefit-card">🎊 금리 인하권 신청 대상입니다! (약 0.5%p 인하 가능)</div>', unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("현재 신용점수", f"{latest['credit_score']}점")
                col_b.metric("최근 월 매출", f"{latest.get('monthly_sales', 0):,}원")
                col_c.metric("총 예상 절감액", f"{latest['saved_amount']:,}원")
                
                st.write("---")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                    st.subheader("📈 신용점수 변화 추이")
                    fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                    fig.update_traces(textposition="top center", textfont_size=20, line=dict(width=5))
                    fig.add_hline(y=840, line_dash="dash", annotation_text="금리인하 기준(840)", line_color="#DAA520")
                    fig.add_hline(y=700, line_dash="dot", annotation_text="정책자금 커트라인(700)", line_color="#EF4444")
                    fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    fig.update_xaxes(type='category')
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                    st.subheader("🏦 점수별 정책자금 한도")
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
                st.info("데이터를 분석하는 중입니다... 사이드바에서 데이터를 입력해 보세요!")

    with tab2:
        st.header(f"🛠️ {current_user} 데이터 관리실")
        st.write("날짜별 데이터를 수정하거나 삭제할 수 있습니다.")
        
        try:
            res_edit = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
            if res_edit.data:
                edit_df = pd.DataFrame(res_edit.data).sort_values("date", ascending=False)
                edit_date = st.selectbox("수정할 날짜를 선택하세요", edit_df['date'].tolist())
                
                row = edit_df[edit_df['date'] == edit_date].iloc[0]
                
                # 우편 봉투(form) 안에는 수정 완료 버튼만 넣기
                with st.form(key=f"edit_form_{edit_date}"):
                    st.subheader(f"📅 {edit_date} 데이터 수정")
                    ec1, ec2 = st.columns(2)
                    e_init = ec1.number_input("대출 당시 점수 수정", value=int(row['initial_score']))
                    e_curr = ec2.number_input("현재 신용점수 수정", value=int(row['credit_score']))
                    e_sales = ec1.number_input("월 매출 수정(원)", value=int(row['monthly_sales']))
                    e_saved = ec2.number_input("절감액 수정(원)", value=int(row['saved_amount']))
                    
                    submit_btn = st.form_submit_button("✅ 수정 완료")
                    
                if submit_btn:
                    supabase.table("financial_data").update({"initial_score": e_init, "credit_score": e_curr, "monthly_sales": e_sales, "saved_amount": e_saved}).eq("id", row['id']).execute()
                    st.success(f"{edit_date} 데이터가 수정되었습니다!")
                    st.rerun()
                
                st.write("---")
                
                # 삭제 버튼은 우편 봉투 밖에 안전하게 빼두기 (에러 해결 완료!)
                if st.button("🗑️ 이 날짜 데이터 삭제 (복구 불가)", type="primary"):
                    supabase.table("financial_data").delete().eq("id", row['id']).execute()
                    st.warning(f"{edit_date} 데이터가 삭제되었습니다!")
                    st.rerun()
            else:
                st.info("수정할 데이터가 없습니다.")
        except Exception as e:
            st.error(f"오류: {e}")

else:
    st.info("왼쪽 메뉴에서 사장님을 먼저 등록하고 선택해주세요.")
