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
            
            # 🚨 폼(봉투) 시작: 여기 안에는 수정 입력칸과 '수정 완료' 버튼만 들어갑니다.
            with st.form(key=f"edit_form_{edit_date}"):
                st.subheader(f"📅 {edit_date} 데이터 수정")
                ec1, ec2 = st.columns(2)
                e_init = ec1.number_input("대출 당시 점수 수정", value=int(row['initial_score']))
                e_curr = ec2.number_input("현재 신용점수 수정", value=int(row['credit_score']))
                e_sales = ec1.number_input("월 매출 수정(원)", value=int(row['monthly_sales']))
                e_saved = ec2.number_input("절감액 수정(원)", value=int(row['saved_amount']))
                
                # 봉투 전용 제출 버튼
                submit_btn = st.form_submit_button("✅ 수정 완료")
                
            # 🚨 폼 밖에서 동작: 수정 로직
            if submit_btn:
                supabase.table("financial_data").update({"initial_score": e_init, "credit_score": e_curr, "monthly_sales": e_sales, "saved_amount": e_saved}).eq("id", row['id']).execute()
                st.success(f"{edit_date} 데이터가 수정되었습니다!")
                st.rerun()
            
            st.write("---")
            
            # 🚨 폼(봉투) 바깥에 삭제 버튼 배치! (에러 해결 핵심)
            if st.button("🗑️ 이 날짜 데이터 삭제 (복구 불가)", type="primary"):
                supabase.table("financial_data").delete().eq("id", row['id']).execute()
                st.warning(f"{edit_date} 데이터가 삭제되었습니다!")
                st.rerun()
        else:
            st.info("수정할 데이터가 없습니다.")
