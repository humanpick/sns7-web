import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 인테리어 설정
st.set_page_config(page_title="SNS7 재무관리 리포트", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #F1F5F9; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    .graph-card { background-color: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #E2E8F0; margin-bottom: 25px; }
    [data-testid="stMetricValue"] { font-size: 3.5rem !important; color: #DAA520 !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.3rem !important; color: #1E3A8A !important; font-weight: bold !important; }
    .benefit-card { background-color: #DAA520; color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 30px; font-weight: bold; font-size: 1.8rem; }
    /* 수정창 입력칸 강조 */
    .stTextInput input, .stNumberInput input { color: black !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바: 기본 고객 선택
with st.sidebar:
    st.title("⚙️ 관리실")
    client_res = supabase.table("clients").select("*").execute()
    if client_res.data:
        names = {c['name']: c['id'] for c in client_res.data}
        selected_name = st.selectbox("📊 조회/수정할 고객 선택", list(names.keys()))
        selected_id = names[selected_name]
    else:
        st.warning("먼저 고객을 등록해주세요.")
        selected_id = None

# [4] 메인 화면: 탭 메뉴 구성
if selected_id:
    # '리포트 보기'와 '데이터 관리(수정)' 두 개의 방을 만듭니다.
    tab1, tab2 = st.tabs(["📈 분석 리포트 확인", "🛠️ 데이터 수정/삭제"])

    with tab1:
        st.header(f"📊 {selected_name} 재무관리 분석")
        try:
            res = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                df = df.sort_values("date")
                latest = df.iloc[-1]
                # 금리 인하 로직 및 상단 요약/그래프 출력 (기존과 동일)
                # ... (지면상 생략, 핵심은 tab1 안에 기존 리포트 코드를 넣는 것)
                is_eligible = (latest['credit_score'] >= 840) or (latest['credit_score'] - latest.get('initial_score', 700) >= 70)
                if is_eligible: st.markdown(f'<div class="benefit-card">🎊 금리 인하권 신청 대상입니다!</div>', unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("현재 신용점수", f"{latest['credit_score']}점")
                col_b.metric("최근 월 매출", f"{latest.get('monthly_sales', 0):,}원")
                col_c.metric("총 예상 절감액", f"{latest['saved_amount']:,}원")
                
                st.divider()
                # 그래프 카드들 (생략하지만 실제 코드에는 포함됨)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                    st.subheader("신용점수 추이")
                    fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                    fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                    st.subheader("매출 성장 추이")
                    fig_sales = px.bar(df, x="date", y="monthly_sales", color_discrete_sequence=["#1E3A8A"])
                    fig_sales.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_sales, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("데이터가 없습니다. 옆의 [데이터 수정/삭제] 탭에서 등록해주세요.")
        except Exception as e: st.error(f"오류: {e}")

    with tab2:
        st.header(f"🛠️ {selected_name} 데이터 관리실")
        st.write("날짜별 데이터를 수정하거나 새로운 날짜의 데이터를 입력할 수 있습니다.")
        
        # 1. 새로운 데이터 추가
        with st.expander("➕ 새로운 날짜 데이터 추가하기"):
            new_date = st.date_input("날짜 선택")
            c1, c2 = st.columns(2)
            s_init = c1.number_input("대출 당시 점수", value=700)
            s_curr = c2.number_input("현재 신용점수", value=750)
            m_sales = c1.number_input("월 매출(원)", value=0, step=100000)
            m_saved = c2.number_input("절감액(원)", value=0, step=10000)
            if st.button("신규 저장"):
                supabase.table("financial_data").insert({"client_id": selected_id, "date": new_date.strftime("%Y-%m"), "initial_score": s_init, "credit_score": s_curr, "monthly_sales": m_sales, "saved_amount": m_saved}).execute()
                st.success("데이터가 추가되었습니다!"); st.rerun()

        st.divider()
        
        # 2. 기존 데이터 수정 및 삭제 (날짜별로 선택)
        res_edit = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
        if res_edit.data:
            edit_df = pd.DataFrame(res_edit.data).sort_values("date", ascending=False)
            edit_date = st.selectbox("수정할 날짜를 선택하세요", edit_df['date'].tolist())
            
            # 선택한 날짜의 기존 값 가져오기
            row = edit_df[edit_df['date'] == edit_date].iloc[0]
            
            with st.form(key=f"edit_form_{edit_date}"):
                st.subheader(f"📅 {edit_date} 데이터 수정")
                ec1, ec2 = st.columns(2)
                e_init = ec1.number_input("대출 당시 점수 수정", value=int(row['initial_score']))
                e_curr = ec2.number_input("현재 신용점수 수정", value=int(row['credit_score']))
                e_sales = ec1.number_input("월 매출 수정(원)", value=int(row['monthly_sales']))
                e_saved = ec2.number_input("절감액 수정(원)", value=int(row['saved_amount']))
                
                col_btn1, col_btn2 = st.columns([1, 4])
                if col_btn1.form_submit_button("✅ 수정 완료"):
                    supabase.table("financial_data").update({"initial_score": e_init, "credit_score": e_curr, "monthly_sales": e_sales, "saved_amount": e_saved}).eq("id", row['id']).execute()
                    st.success(f"{edit_date} 데이터가 수정되었습니다!"); st.rerun()
                
                if st.button("🗑️ 이 날짜 데이터 삭제", help="삭제하면 복구할 수 없습니다."):
                    supabase.table("financial_data").delete().eq("id", row['id']).execute()
                    st.warning(f"{edit_date} 데이터가 삭제되었습니다!"); st.rerun()
        else:
            st.info("수정할 데이터가 없습니다.")

else:
    st.info("왼쪽 메뉴에서 사장님을 먼저 선택해주세요!")
