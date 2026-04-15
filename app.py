import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# [1] 창고 열쇠
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 💡 한국어 돈 단위 변환 함수 
def format_krw(val):
    if pd.isna(val) or val == 0: return "0원"
    val = int(val)
    if val >= 100000000:
        eok = val // 100000000
        man = (val % 100000000) // 10000
        return f"{eok}억 {man}만 원" if man else f"{eok}억 원"
    elif val >= 10000:
        return f"{val//10000}만 원" if val % 10000 == 0 else f"{val//10000}만 {val%10000}원"
    return f"{val:,}원"

# [2] 명품 디자인 설정 (에메랄드 그린 포인트)
st.set_page_config(page_title="SNS7 재무관리 리포트", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #F1F5F9; }
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: bold !important; }
    
    .top-notice {
        background-color: #EF4444; color: white; padding: 15px; border-radius: 10px;
        text-align: center; font-size: 1.5rem; font-weight: 900; margin-bottom: 20px;
    }
    
    .graph-card {
        background-color: white; padding: 30px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0; margin-bottom: 25px;
    }

    /* 💡 1. 타이틀(이름) 폰트 크기 축소 */
    h1 { font-size: 2.2rem !important; }

    /* 💡 2. 상단 숫자(신용점수, 매출 등) 크기 축소 & 컬러 변경 (에메랄드 그린) */
    [data-testid="stMetricValue"] { font-size: 3.2rem !important; color: #059669 !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; color: #1E3A8A !important; font-weight: 900 !important; }

    /* 혜택 카드도 에메랄드 그린으로 통일 */
    .benefit-card {
        background-color: #059669; color: white; padding: 25px; border-radius: 20px;
        text-align: center; margin-bottom: 30px; font-weight: bold; font-size: 1.8rem;
    }
    
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
    st.markdown('<div class="top-notice">📢 신용점수 839점 이하: 신용취약 소상공인 정책자금 신청 가능!</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📈 분석 리포트", "🛠️ 데이터 수정/삭제"])

    with tab1:
        st.title(f"📊 {current_user} 재무관리 리포트")
        res = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df = df.sort_values("date")
            latest = df.iloc[-1]
            c_score = latest['credit_score']
            
            is_eligible = (c_score >= 840) or (c_score - latest.get('initial_score', 700) >= 70)
            if is_eligible:
                st.markdown(f'<div class="benefit-card">🎊 금리 인하권 획득! 대출 금리 0.5%p 즉시 인하 가능</div>', unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("현재 신용점수", f"{c_score}점")
            col_b.metric("최근 월 매출", format_krw(latest.get('monthly_sales', 0)))
            col_c.metric("총 절감 성과", format_krw(latest['saved_amount']))
            
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("📈 신용점수 변화 추이")
                # 💡 선 그래프도 에메랄드 그린으로 변경
                fig = px.line(df, x="date", y="credit_score", markers=True, text="credit_score", color_discrete_sequence=["#059669"])
                fig.update_traces(textposition="top center", textfont_size=28, textfont_color="#1E3A8A", line=dict(width=7), marker=dict(size=15))
                fig.add_hline(y=840, line_dash="dash", annotation_text="금리인하/정상회복(840)", line_color="#059669", annotation_font_size=18)
                fig.add_hline(y=700, line_dash="dot", annotation_text="정책자금 커트라인(700)", line_color="#EF4444", annotation_font_size=18)
                
                fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"), dragmode=False)
                fig.update_xaxes(type='category', fixedrange=True)
                fig.update_yaxes(fixedrange=True)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("🏦 점수별 정책자금 지원 한도")
                
                tiers = ["839점 이하", "840점 이상"]
                limits = [30, 100] 
                labels = ["최대 3,000만 원", "1억 원 이상(민간)"]
                
                fund_df = pd.DataFrame({"구간": tiers, "한도": limits, "설명": labels})
                fig_f = px.bar(fund_df, x="구간", y="한도", text="설명", color="구간", 
                               color_discrete_map={
                                   "839점 이하": "#38BDF8", 
                                   "840점 이상": "#FDE047"   
                               })
                fig_f.update_traces(textposition="outside", textfont_size=24, textfont_color="#1E3A8A")
                
                fig.update_layout(height=500, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"), dragmode=False)
                fig_f.update_xaxes(fixedrange=True)
                fig_f.update_yaxes(visible=False, fixedrange=True) 
                st.plotly_chart(fig_f, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            latest_date_obj = pd.to_datetime(latest['date'])
            six_months = [(latest_date_obj - pd.DateOffset(months=i)).strftime('%Y-%m') for i in range(5, -1, -1)]

            col3, col4 = st.columns(2)
            with col3:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("📊 월별 매출 성장 추이 (최근 6개월)")
                df['sales_krw'] = df['monthly_sales'].apply(format_krw)
                fig_sales = px.bar(df, x="date", y="monthly_sales", text="sales_krw", color_discrete_sequence=["#1E3A8A"])
                fig_sales.update_traces(textfont_size=20, textfont_color="white", textposition="inside", width=0.4)
                
                fig_sales.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"), dragmode=False)
                fig_sales.update_xaxes(type='category', categoryorder='array', categoryarray=six_months, fixedrange=True)
                fig_sales.update_yaxes(visible=False, fixedrange=True)
                st.plotly_chart(fig_sales, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            with col4:
                st.markdown('<div class="graph-card">', unsafe_allow_html=True)
                st.subheader("💰 월별 경영 비용 절감액 (최근 6개월)")
                df['saved_krw'] = df['saved_amount'].apply(format_krw)
                # 💡 절감액 막대 그래프도 에메랄드 그린으로 변경
                fig_saved = px.bar(df, x="date", y="saved_amount", text="saved_krw", color_discrete_sequence=["#059669"])
                fig_saved.update_traces(textfont_size=20, textfont_color="black", textposition="outside", width=0.4)
                
                fig_saved.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=18, weight="bold"), dragmode=False)
                fig_saved.update_xaxes(type='category', categoryorder='array', categoryarray=six_months, fixedrange=True)
                fig_saved.update_yaxes(visible=False, fixedrange=True)
                st.plotly_chart(fig_saved, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.header(f"🛠️ {current_user} 데이터 관리실")
        res_edit = supabase.table("financial_data").select("*").eq("client_id", selected_id).execute()
        if res_edit.data:
            edit_df = pd.DataFrame(res_edit.data).sort_values("date", ascending=False)
            
            st.subheader("1. 수정할 날짜 선택")
            target_date = st.selectbox("수정을 원하는 날짜를 골라주세요", edit_df['date'].tolist())
            row = edit_df[edit_df['date'] == target_date].iloc[0]

            st.write("---")
            st.subheader(f"2. {target_date} 데이터 수정")
            with st.form(key=f"edit_form_{target_date}"):
                c1, c2 = st.columns(2)
                u_init = c1.number_input("대출 당시 점수", value=int(row['initial_score']))
                u_curr = c2.number_input("현재 신용점수", value=int(row['credit_score']))
                u_sales = c1.number_input("월 매출(원)", value=int(row['monthly_sales']), step=1000000)
                u_saved = c2.number_input("절감액(원)", value=int(row['saved_amount']), step=10000)
                
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
            m_s = sc1.number_input("월 매출(원) ", value=0, step=1000000)
            m_v = sc2.number_input("절감액(원) ", value=0, step=10000)
            if st.button("새 데이터 저장"):
                supabase.table("financial_data").insert({
                    "client_id": selected_id, "date": new_d.strftime("%Y-%m"),
                    "initial_score": i_s, "credit_score": c_s,
                    "monthly_sales": m_s, "saved_amount": m_v
                }).execute()
                st.success("저장됨"); st.rerun()
