import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# [2] 명품 디자인 설정
st.set_page_config(page_title="SNS7 재무관리 리포트", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #F1F5F9; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    
    /* 최상단 강조 알림창 */
    .top-notice {
        background-color: #EF4444; color: white; padding: 15px; border-radius: 10px;
        text-align: center; font-size: 1.5rem; font-weight: 900; margin-bottom: 20px;
    }
    
    .graph-card {
        background-color: white; padding: 30px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0; margin-bottom: 25px;
    }

    [data-testid="stMetricValue"] { font-size: 4.2rem !important; color: #DAA520 !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.6rem !important; color: #1E3A8A !important; font-weight: 900 !important; }

    .benefit-card {
        background-color: #DAA520; color: white; padding: 25px; border-radius: 20px;
        text-align: center; margin-bottom: 30px; font-weight: bold; font-size: 2rem;
    }
    
    /* 입력창 글자 찐하게 */
    input { color: black !important; font-weight: bold !important; font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# [3] 사이드바 관리 메뉴
with st.sidebar:
    st.title("⚙️ 관리실")
    with st.expander("👤 새 사장님 등록"):
        n_name = st.text_input("성함/상호명")
        if st.button("등록"):
            if n_name:
                supabase.table("clients").insert({"name": n_name}).execute()
                st.success("등록됨"); st.rerun()

    client_res = supabase.table("clients").select("*").execute()
    if client_res.data:
        view_names = {c['name']: c['id'] for c in client_res.data}
        current_user = st.selectbox("📊 리포트 대상 선택", list(view_names.keys()))
        selected_id = view_names[current_user]
    else:
        current_user, selected_id = None, None

# [4] 메인 화면
if current_user:
    # 💡 839점 이하 안내문구 최상단 배치
    st.markdown('<div class="top-notice">📢 신용점수 839점 이하: 신용취약 소상공인 정책자금 신청 가능!</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📈 분석 리포트", "🛠️ 데이터 수정/삭제"])

    with tab1:
        st.title(f"📊 {current_user} 재무관리 분석 리포트")
        res = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")
            latest = df.iloc[-1]
            c_score = latest['credit_score']
            
            # 금리 인하권 감지 로직 (+70점 혹은 840점 이상)
            is_eligible = (c_score >= 840) or (c_score - latest.get('initial_score', 700) >= 70)
            if is_eligible:
                st.markdown(f'<div class="benefit-card">🎊 금리 인하권 획득! 대출 금리 0.5%p 즉시 인하 가능</div>', unsafe_allow_html=True)

            # 상단 핵심 지표
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("현재 신용점수", f"{c_score}점")
            col_b.metric("최근 월 매출", f"{latest.get('monthly_sales', 0):,}원")
            col_c.metric("총 절감 성과", f"{latest['saved_amount']:,}원")
            
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("📈 신용점수 변화 추이")
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#DAA520"])
                # 폰트 대폭 상향 및 찐한 네이비색
                fig.update_traces(textposition="top center", textfont_size=28, textfont_color="#1E3A8A", line=dict(width=7), marker=dict(size=15))
                fig.add_hline(y=840, line_dash="dash", annotation_text="금리인하/정상회복(840)", line_color="#DAA520", annotation_font_size=18)
                fig.add_hline(y=700, line_dash="dot", annotation_text="정책자금 커트라인(700)", line_color="#EF4444", annotation_font_size=18)
                fig.update_layout(height=550, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"))
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("🏦 점수별 정책자금 지원 한도")
                # 민준님 정보 반영: 839점 이하 최대 3,000만원
                tiers = ["840점 이상", "839점 이하"]
                limits = [10, 30] # 단위: 백만
                labels = ["민간 자금 권장", "최대 3,000만 원"]
                
                my_t = tiers[1] if c_score <= 839 else tiers[0]
                fund_df = pd.DataFrame({"구간": tiers, "한도": limits, "설명": labels})
                fund_df["색상"] = fund_df["구간"].apply(lambda x: "#DAA520" if x == my_t else "#E2E8F0")
                
                fig_f = px.bar(fund_df, x="구간", y="한도", text="설명", color="색상", color_discrete_map="identity")
                fig_f.update_traces(textposition="outside", textfont_size=24, textfont_color="#1E3A8A")
                fig_f.update_layout(height=550, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"))
                fig_f.update_yaxes(visible=False)
                st.plotly_chart(fig_f, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.header(f"🛠️ {current_user} 데이터 관리실")
        # 데이터가 안 고쳐질 때는 '날짜'를 정확히 선택했는지 확인해야 합니다.
        res_edit = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
        if res_edit.data:
            edit_df = pd.DataFrame(res_edit.data).sort_values("date", ascending=False)
            
            # 수정할 날짜를 먼저 선택하게 합니다.
            st.subheader("1. 수정할 날짜 선택")
            target_date = st.selectbox("수정을 원하는 날짜를 골라주세요", edit_df['date'].tolist())
            row = edit_df[edit_df['date'] == target_date].iloc[0]

            st.write("---")
            st.subheader(f"2. {target_date} 데이터 수정")
            # 폼을 사용하여 안전하게 전송
            with st.form(key=f"edit_form_{target_date}"):
                c1, c2 = st.columns(2)
                u_init = c1.number_input("대출 당시 점수", value=int(row['initial_score']))
                u_curr = c2.number_input("현재 신용점수", value=int(row['credit_score']))
                u_sales = c1.number_input("월 매출(원)", value=int(row['monthly_sales']))
                u_saved = c2.number_input("절감액(원)", value=int(row['saved_amount']))
                
                if st.form_submit_button("✅ 이 날짜 데이터 수정 완료"):
                    supabase.table("financial_data").update({
                        "initial_score": u_init, "credit_score": u_curr,
                        "monthly_sales": u_sales, "saved_amount": u_saved
                    }).eq("id", row['id']).execute()
                    st.success("수정되었습니다!"); st.rerun()

            st.write("---")
            if st.button("🗑️ 이 날짜 데이터 완전히 삭제", type="primary"):
                supabase.table("financial_data").delete().eq("id", row['id']).execute()
                st.warning("삭제되었습니다!"); st.rerun()
        else:
            st.info("수정할 데이터가 없습니다.")

        st.divider()
        with st.expander("➕ 새로운 날짜 데이터 추가"):
            new_d = st.date_input("기준 날짜")
            sc1, sc2 = st.columns(2)
            i_s = sc1.number_input("대출 당시 점수 ", value=700)
            c_s = sc2.number_input("현재 신용점수 ", value=750)
            m_s = sc1.number_input("월 매출(원) ", value=0)
            m_v = sc2.number_input("절감액(원) ", value=0)
            if st.button("새 데이터 저장"):
                supabase.table("financial_data").insert({
                    "client_id": selected_id, "date": new_d.strftime("%Y-%m"),
                    "initial_score": i_s, "credit_score": c_s,
                    "monthly_sales": m_s, "saved_amount": m_v
                }).execute()
                st.success("저장됨"); st.rerun()
