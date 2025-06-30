# doctor_dashboard.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
load_dotenv()
from embedding import store_question_answer
import os
import json

firebase_config = st.secrets["FIREBASE_CONFIG"]

if isinstance(firebase_config, str):
    firebase_config = json.loads(firebase_config)

# Convert to a proper JSON-like dictionary (optional: write to temp file)
with open("firebase_temp.json", "w") as f:
    json.dump(firebase_config, f)

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_temp.json")
    firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

def doctor_dashboard():
    st.title("🏥 Doctor Dashboard")
    
    # Initialize session state for navigation
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'unanswered'
    
    # Navigation buttons
    section = st.sidebar.radio(
        "Navigation",
        ("📋 Unanswered Questions", "💬 User Queries", "➕ Add Q&A"),
        index=0 if st.session_state.current_section == 'unanswered' else (1 if st.session_state.current_section == 'queries' else 2)
    )
    
    # Update session state based on selection
    if section == "📋 Unanswered Questions":
        st.session_state.current_section = 'unanswered'
    elif section == "💬 User Queries":
        st.session_state.current_section = 'queries'
    else:
        st.session_state.current_section = 'add_qa'
    
    st.markdown("---")
    
    # Display content based on selected section
    if st.session_state.current_section == 'unanswered':
        display_unanswered_questions()
    elif st.session_state.current_section == 'queries':
        display_user_queries()
    elif st.session_state.current_section == 'add_qa':
        display_add_qa()

def display_unanswered_questions():
    st.subheader("📌 Unanswered Questions")
    
    # Reference to the doctor document
    doctor_doc_ref = db.collection("DOCTOR").document("1")  # Adjust the document path as needed

    try:
        # Fetch data from Firestore
        doc = doctor_doc_ref.get()
        data = doc.to_dict() if doc.exists else {}

        qn_list = data.get("qn", [])
        ans_dict = data.get("ans", {})

        # ✅ Fix: Ensure ans_dict is always a dictionary
        if not isinstance(ans_dict, dict):
            ans_dict = {}

        # Separate Answered & Unanswered Questions
        answered_qs = {q: ans_dict[q] for q in qn_list if q in ans_dict}
        unanswered_qs = [q for q in qn_list if q not in ans_dict]

        # Display Unanswered Questions with Input Box
        if unanswered_qs:
            st.write(f"**Total Unanswered Questions:** {len(unanswered_qs)}")
            st.markdown("---")
            
            for i, q in enumerate(unanswered_qs, 1):
                with st.container():
                    st.write(f"**Question {i}:** {q}")
                    answer = st.text_area(f"Enter your answer:", key=f"answer_{q}", height=100)
                    
                    if st.button(f"Submit Answer", key=f"btn_{q}", type="primary"):
                        if answer.strip():
                            try:
                                store_question_answer(q, answer)
                                doctor_doc_ref.set({
                                    "ans": {**ans_dict, q: answer}  # ✅ Now always a dictionary
                                }, merge=True)
                                st.success("✅ Answer saved successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error saving answer: {str(e)}")
                        else:
                            st.warning("⚠️ Please enter a valid answer.")
                    
                    st.markdown("---")
        else:
            st.success("✅ No pending unanswered questions!")

    except Exception as e:
        st.error(f"❌ Error fetching data from Firebase: {str(e)}")
        st.info("Please check your Firebase configuration and connection.")

def display_user_queries():
    st.subheader("💬 User Queries")
    
    try:
        # Fetch user interactions from Firebase
        user_queries_ref = db.collection("user").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50)
        queries = user_queries_ref.stream()
        
        # Convert to list for easier processing
        query_list = []
        for query in queries:
            query_data = query.to_dict()
            query_data['id'] = query.id
            query_list.append(query_data)
        
        if not query_list:
            st.info("📭 No user queries found.")
            return
        
        # Display queries
        for i, query in enumerate(query_list, 1):
            with st.expander(f"Query {i}: {query.get('question', 'N/A')[:60]}..."):
                
                # Question
                st.write(f"**Question:** {query.get('question', 'N/A')}")
                
                # Answer
                st.write(f"**Answer:** {query.get('answer', 'N/A')}")
    
    except Exception as e:
        st.error(f"❌ Error fetching user queries: {str(e)}")
        st.info("Please check your Firebase configuration and connection.")

def display_add_qa():
    st.subheader("➕ Add Question & Answer")
    st.write("Manually add question-answer pairs to the knowledge base.")
    
    # Create form for adding Q&A
    with st.form("add_qa_form"):
        st.markdown("### 📝 Enter Question & Answer")
        
        # Question input
        question = st.text_area(
            "Question:",
            placeholder="Enter the question here...",
            height=100,
            help="Enter a clear and specific question"
        )
        
        # Answer input
        answer = st.text_area(
            "Answer:",
            placeholder="Enter the detailed answer here...",
            height=150,
            help="Provide a comprehensive answer to the question"
        )
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Question & Answer", type="primary")
        
        if submitted:
            # Validate inputs
            if not question.strip():
                st.error("❌ Please enter a question.")
            elif not answer.strip():
                st.error("❌ Please enter an answer.")
            else:
                try:
                    # Show loading spinner
                    with st.spinner("Saving question and answer..."):
                        # Call the store_question_answer function
                        store_question_answer(question.strip(), answer.strip())
                    
                    # Success message
                    st.success("✅ Question and answer saved successfully!")
                    
                    # Display what was saved
                    st.markdown("### 📋 Saved Information:")
                    st.write(f"**Question:** {question.strip()}")
                    st.write(f"**Answer:** {answer.strip()}")
                    
                except Exception as e:
                    st.error(f"❌ Error saving question and answer: {str(e)}")
                    st.info("Please check your database connection and try again.")

# Call the doctor dashboard function if this file is run directly
if __name__ == "__main__":
    doctor_dashboard()
