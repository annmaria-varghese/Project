# ------------------- Quiz -------------------
if quiz_clicked and st.session_state.get('last_summary'):
    st.session_state['quiz_started'] = True
    st.session_state['quiz_score'] = 0
    st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['last_summary'][0], n_questions=5)
    # Prepare placeholders for user answers
    if 'user_answers' not in st.session_state:
        st.session_state['user_answers'] = [""] * len(st.session_state['quiz_questions'])

if st.session_state.get('quiz_started'):
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    
    for idx, q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        st.session_state['user_answers'][idx] = st.radio("Select answer:", q['options'], key=f"q{idx}", index=q['options'].index(st.session_state['user_answers'][idx]) if st.session_state['user_answers'][idx] in q['options'] else 0)
    
    if st.button("Submit Quiz"):
        score = 0
        for idx, q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['user_answers'][idx] == q['answer']:
                score += 1
        st.session_state['quiz_score'] = score
        
        # Show detailed results
        for idx, q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['user_answers'][idx] == q['answer']:
                st.success(f"Q{idx+1}: Correct! ✅")
            else:
                st.error(f"Q{idx+1}: Wrong ❌ — {q['explanation']}")
        st.markdown(f"**Your Total Score: {st.session_state['quiz_score']} / {len(st.session_state['quiz_questions'])}**")
