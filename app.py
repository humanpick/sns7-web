import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# 1. 로봇의 열쇠 꾸러미 (수정 금지)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 2. 웹사이트 명품 테마 설정 (세련된 네이비 & 골드)
st.set_page_config(
    page_title="SNS7 CEO 포털", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 스타일 (CSS) 적용 ---
# 배경색을 밝은 네이비(연한 그레이 블루)로, 글자색을 짙은 네이비로 설정합니다.
st.markdown("""
<style>
    /* 메인 화면 배경색 및 글자색 */
    .stApp {
        background-color: #F0F2F6; /* 아주 연한 그레이 블루 (어둡지 않은 네이비 느낌) */
        color: #1E3A8A; /* 짙은 네이비 (텍스트) */
    }
    
    /* 사이드바 배경색 및 글자색 */
    [data-testid="stSidebar"] {
        background-color: #1E3A8A; /* 짙은 네이비 */
        color: white; /* 사이드바 텍스트는 흰색 */
    }
    [data-testid="stSidebar"] * {
        color: white;
    }

    /* 제목(H1, H2, H3) 색상 */
    h1, h2, h3 {
        color: #1E3A8A; /* 짙은 네이비 */
        font-weight: 700;
    }

    /* 버튼 스타일 (골드 포인트) */
    .stButton>button {
        background-color: #DAA520; /* 골드 (Goldenrod) */
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #B8860B; /* 마우스 올렸을 때 더 짙은 골드 */
        color: white;
    }
</style>
""", unsafe_content_with_escape=True)


# 3. 메인 화면 구성
st.title("📊 SNS7 경영지원 실시간 리포트")
st.write(f"### **민준 대표님**, 환영합니다! 현재 경영 상태를 분석했습니다.")
st.divider()

# 4. 보물상자에서 데이터 꺼내오기
try:
    res = supabase.table("financial_data").select("*").execute()
    data = res.data

    if data:
        # 데이터 뭉치(JSON)를 표(DataFrame)로 변환하기
        df = pd.DataFrame(data)
        
        # 날짜순으로 정렬 (혹시 순서가 섞여있을까봐요!)
        df = df.sort_values(by="date")

        # 화면을 반으로 나눠서 그래프 두 개 그리기
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 신용점수 변화")
            # 선 그래프 그리기 (골드 색상 적용)
            fig_credit = px.line(df, x="date", y="credit_score", 
                                 markers=True, text="credit_score",
                                 color_discrete_sequence=["#DAA520"]) # 골드
            fig_credit.update_traces(textposition="top center", line=dict(width=3))
            
            # 그래프 배경도 세련되게 투명으로 설정
            fig_credit.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1E3A8A") # 짙은 네이비 글자
            )
            st.plotly_chart(fig_credit, use_container_width=True)

        with col2:
            st.subheader("💰 예상 절감액 (누적)")
            # 막대 그래프 그리기 (골드 색상 적용)
            fig_saved = px.bar(df, x="date", y="saved_amount", 
                               text_auto=True,
                               color_discrete_sequence=["#DAA520"]) # 골드
            
            # 그래프 배경 투명 설정
            fig_saved.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1E3A8A") # 짙은 네이비 글자
            )
            st.plotly_chart(fig_saved, use_container_width=True)

        # 아래쪽에 상세 표 보여주기
        st.divider()
        st.subheader("📋 상세 데이터 확인")
        # 표 스타일도 네이비&흰색으로 깔끔하게
        st.dataframe(df[['date', 'credit_score', 'saved_amount']], use_container_width=True)

    else:
        st.warning("상자에 보물은 있는데 내용물이 비어있어요!")

except Exception as e:
    st.error(f"로봇이 그림을 그리다가 실수했어요: {e}")

# 5. 사이드바 구성 (짙은 네이비 배경에 흰색 글자)
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.write("데이터를 최신 상태로 유지하세요.")
    if st.button("🔄 데이터 새로고침"):
        st.rerun()
