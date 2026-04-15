import streamlit as st
from supabase import create_client

# 1. 로봇에게 열쇠 보여주기
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    st.success("✅ 로봇이 열쇠를 잘 받았어요!")
except:
    st.error("❌ 로봇이 열쇠가 가짜라고 해요. Secrets 설정을 확인해주세요.")

# 2. 상자 열어보기
st.title("민준 대표님의 보물지도")

try:
    # 상자에서 데이터 꺼내기
    res = supabase.table("financial_data").select("*").execute()
    
    if len(res.data) == 0:
        st.warning("⚠️ 상자는 열었는데, 안에 색연필(데이터)이 하나도 없어요!")
    else:
        st.write("🎉 와! 색연필을 찾았어요!")
        st.write(res.data) # 데이터가 보이면 성공!
except Exception as e:
    st.error(f"❌ 상자 여는 게 너무 어려워요. 이유: {e}")
