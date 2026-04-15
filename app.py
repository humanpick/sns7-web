import streamlit as st
from supabase import create_client
import plotly.express as px
import pandas as pd

# 1. ȯ�� ���� (Supabase ����)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# 2. ������ ���� �� ���̵��
st.set_page_config(page_title="���� ������ CEO ����", layout="wide")

def main():
    if "user" not in st.session_state:
        show_login_page()
    else:
        show_dashboard()

# 3. īī�� �α��� ������
def show_login_page():
    st.title("?? ���� ������ �濵���� ����")
    st.write("������� �繫 �ǰ��� ���ڷ� Ȯ���ϼ���.")
    
    if st.button("īī���� 1�� ���� �����ϱ�"):
        # Supabase�� ���� īī�� OAuth ���� ȣ��
        res = supabase.auth.sign_in_with_oauth({
            "provider": "kakao",
            "options": {"redirect_to": "https://your-domain.com"}
        })
        st.write("�α��� �������� �̵� ��...")

# 4. ���� ���� ��ú��� (�ٽ� ���)
def show_dashboard():
    user = st.session_state.user
    st.sidebar.title(f"?? {user['name']} �����")
    
    menu = st.sidebar.selectbox("�޴� ����", ["�繫 ��ú���", "���� ���𵨸�", "�ڱ� ��û ��Ȳ"])

    if menu == "�繫 ��ú���":
        st.header("?? ���� �繫 ���� ����")
        
        # DB���� ������ �ҷ����� (���� ������)
        data = fetch_financial_data(user['id'])
        df = pd.DataFrame(data)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("�ſ����� ��ȭ")
            fig_credit = px.line(df, x="date", y="credit_score", markers=True)
            st.plotly_chart(fig_credit, use_container_width=True)
            
        with col2:
            st.subheader("�� ���� ���� ������")
            fig_fee = px.bar(df, x="date", y="saved_amount", color="date")
            st.plotly_chart(fig_fee, use_container_width=True)

    elif menu == "���� ���𵨸�":
        st.subheader("?? ���� ���� �м� ���")
        st.info("���� �м��� ����Ʈ�� 1�� �ֽ��ϴ�. Ȯ�� ��ư�� �����ּ���.")

# 5. ������ �ҷ����� �Լ� (���� DB ����)
def fetch_financial_data(user_id):
    # ���� � �� supabase.table("financial_data").select("*").eq("user_id", user_id).execute() ���
    return [
        {"date": "2026-01", "credit_score": 633, "saved_amount": 0},
        {"date": "2026-02", "credit_score": 650, "saved_amount": 120000},
        {"date": "2026-03", "credit_score": 685, "saved_amount": 250000},
    ]

if __name__ == "__main__":
    main()