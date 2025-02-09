import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

# Debug prints
print("Attempting Firebase initialization...")
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate('credentials.json')
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
    db = firestore.client()
    print("Firestore client created")
except Exception as e:
    print(f"Firebase initialization error: {str(e)}")
    st.error(f"Firebase initialization failed: {str(e)}")

# Collections references
questions_ref = db.collection('questions')
responses_ref = db.collection('responses')
users_ref = db.collection('users')

# Page Configuration
st.set_page_config(
    page_title="MagnusMinds Quiz",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .quiz-header {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header {
        background-color: #2C3E50;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def main_header():
    st.markdown('<div class="main-header">MagnusMinds Quiz</div>', unsafe_allow_html=True)

def signup():
    main_header()
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title("📝 Sign Up")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Choose a Username:")
        password = st.text_input("Choose a Password:", type="password")
    with col2:
        role = st.selectbox("Select Role:", ["user", "admin"])
        st.write("")
        st.write("")
    
    if st.button("Sign Up", key="signup_button"):
        if not username or not password:
            st.error("Please fill in all fields")
            return
            
        user_doc = users_ref.where('username', '==', username).limit(1).get()
        if len(list(user_doc)) > 0:
            st.error("Username already exists. Choose another.")
        else:
            try:
                users_ref.add({
                    "username": username,
                    "password": password,
                    "role": role,
                    "created_at": datetime.now()
                })
                st.success("Account created successfully! Please log in.")
            except Exception as e:
                st.error(f"An error occurred during signup: {str(e)}")
                print(f"Signup error: {str(e)}")

def login():
    main_header()
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title("🔐 Login")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username:")
    with col2:
        password = st.text_input("Password:", type="password")
    
    if st.button("Login", key="login_button"):
        if not username or not password:
            st.error("Please fill in all fields")
            return
            
        try:
            user_query = users_ref.where('username', '==', username).where('password', '==', password).limit(1).get()
            user_docs = list(user_query)
            if user_docs:
                user_data = user_docs[0].to_dict()
                user_data['id'] = user_docs[0].id
                st.session_state["user"] = user_data
                st.success(f"Welcome back, {username}!")
            else:
                st.error("Invalid credentials")
        except Exception as e:
            st.error(f"An error occurred during login: {str(e)}")
            print(f"Login error: {str(e)}")

def admin_panel():
    main_header()
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title("👨‍💼 Admin Panel - Manage Quiz")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    
    quiz_name = st.text_input("Enter Quiz Name:")
    
    try:
        question_count = len(list(questions_ref.where('quiz_name', '==', quiz_name).get()))
        st.metric("Total Questions Added", question_count)
        st.write("Quiz Status:", "✅ Active" if question_count > 0 else "⏳ Draft")
    except Exception as e:
        st.error(f"Error loading question count: {str(e)}")
        question_count = 0
    
    st.divider()
    
    st.subheader("Add New Question")
    question = st.text_input("Enter Question:")
    col1, col2 = st.columns(2)
    with col1:
        options = [st.text_input(f"Option {i+1}") for i in range(4)]
    with col2:
        correct_option = st.selectbox("Select Correct Option:", options if all(options) else [""])
        points = st.number_input("Points for this question:", min_value=1, value=1)
    
    if st.button("Add to Quiz"):
        if not quiz_name:
            st.error("Please enter a quiz name")
            return
            
        if all(options) and question and correct_option:
            st.session_state.quiz_questions.append({
                "quiz_name": quiz_name,
                "question": question,
                "options": options,
                "correct": correct_option,
                "points": points,
                "votes": {opt: 0 for opt in options}
            })
            st.success("Question added to quiz!")
            st.rerun()
        else:
            st.error("Please fill all fields")
    
    if st.session_state.quiz_questions:
        st.divider()
        st.subheader("Questions to be Added")
        for idx, q in enumerate(st.session_state.quiz_questions):
            with st.expander(f"Question {idx + 1}: {q['question']}", expanded=False):
                st.write("Options:", q["options"])
                st.write("Correct Answer:", q["correct"])
                st.write("Points:", q["points"])
                if st.button(f"Remove Question {idx + 1}"):
                    st.session_state.quiz_questions.pop(idx)
                    st.rerun()
        
        if st.button("Submit Quiz", type="primary"):
            if quiz_name:
                try:
                    for q in st.session_state.quiz_questions:
                        questions_ref.add({
                            **q,
                            "created_at": datetime.now()
                        })
                    st.success(f"Quiz '{quiz_name}' created successfully with {len(st.session_state.quiz_questions)} questions!")
                    st.session_state.quiz_questions = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Error submitting quiz: {str(e)}")
            else:
                st.error("Please enter a quiz name")

def available_quizzes():
    main_header()
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title("📚 Available Quizzes")
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        # Get all quiz documents and filter out any without a quiz_name
        quiz_docs = questions_ref.stream()
        quizzes = set()
        for doc in quiz_docs:
            quiz_data = doc.to_dict()
            if 'quiz_name' in quiz_data and quiz_data['quiz_name']:
                quizzes.add(quiz_data['quiz_name'])
        
        if not quizzes:
            st.warning("No quizzes available. Please check back later.")
            return
        
        for quiz in quizzes:
            try:
                question_count = len(list(questions_ref.where('quiz_name', '==', quiz).get()))
                col1, col2 = st.columns([3,1])
                with col1:
                    st.subheader(quiz)
                    st.write(f"Total Questions: {question_count}")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("Start Quiz", key=f"start_{quiz}"):
                        st.session_state["current_quiz"] = quiz
                        st.session_state["quiz_started"] = True
                        st.rerun()
                st.divider()
            except Exception as e:
                st.error(f"Error loading quiz '{quiz}': {str(e)}")
                print(f"Error in quiz display: {str(e)}")
                
    except Exception as e:
        st.error("An error occurred while loading quizzes. Please try again later.")
        print(f"Error in available_quizzes: {str(e)}")

def play_quiz():
    main_header()
    if "quiz_started" not in st.session_state or not st.session_state["quiz_started"]:
        st.warning("Please select a quiz first.")
        return
    
    quiz_name = st.session_state["current_quiz"]
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title(f"🎯 Quiz: {quiz_name}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        questions_query = questions_ref.where('quiz_name', '==', quiz_name).stream()
        questions = [doc.to_dict() for doc in questions_query]
        
        if not questions:
            st.warning("No questions available for this quiz.")
            return
        
        if "user_responses" not in st.session_state:
            st.session_state.user_responses = {}
        
        for idx, q in enumerate(questions):
            st.write(f"Question {idx + 1} of {len(questions)}")
            st.write(q["question"])
            response = st.radio("Select your answer:", q["options"], key=f"q_{idx}")
            st.session_state.user_responses[q["question"]] = response
            st.divider()
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Submit Quiz", type="primary"):
                submit_quiz(questions, st.session_state.user_responses)
                
    except Exception as e:
        st.error(f"An error occurred while loading the quiz: {str(e)}")
        print(f"Error in play_quiz: {str(e)}")

def submit_quiz(questions, user_responses):
    try:
        total_points = sum(q["points"] for q in questions)
        user_points = 0
        
        for q in questions:
            if q["question"] in user_responses and user_responses[q["question"]] == q["correct"]:
                user_points += q["points"]
        
        score_percentage = (user_points / total_points) * 100 if total_points > 0 else 0
        
        for q in questions:
            if q["question"] in user_responses:
                selected_option = user_responses[q["question"]]
                q_doc = questions_ref.where('question', '==', q["question"]).limit(1).get()[0]
                current_votes = q_doc.to_dict()['votes']
                current_votes[selected_option] += 1
                questions_ref.document(q_doc.id).update({'votes': current_votes})
        
        responses_ref.add({
            "quiz": st.session_state["current_quiz"],
            "user": st.session_state["user"]["username"],
            "responses": user_responses,
            "score": score_percentage,
            "submitted_at": datetime.now()
        })
        
        st.success(f"Quiz Submitted! Your score: {score_percentage:.1f}%")
        
        st.session_state.pop("quiz_started", None)
        st.session_state.pop("current_quiz", None)
        st.session_state.pop("user_responses", None)
        
        if st.button("Back to Available Quizzes"):
            st.rerun()
            
    except Exception as e:
        st.error(f"An error occurred while submitting the quiz: {str(e)}")
        print(f"Error in submit_quiz: {str(e)}")

def view_results():
    main_header()
    st.markdown("<div class='quiz-header'>", unsafe_allow_html=True)
    st.title("📊 Quiz Results Dashboard")
    st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        # Get all quizzes with proper error handling
        quiz_docs = questions_ref.stream()
        quizzes = set()
        for doc in quiz_docs:
            quiz_data = doc.to_dict()
            if 'quiz_name' in quiz_data and quiz_data['quiz_name']:
                quizzes.add(quiz_data['quiz_name'])
        
        if not quizzes:
            st.warning("No quizzes found in the database.")
            return
            
        selected_quiz = st.selectbox("Select Quiz:", list(sorted(quizzes)))
        
        if selected_quiz:
            col1, col2 = st.columns(2)
            responses_query = responses_ref.where('quiz', '==', selected_quiz).stream()
            responses = list(responses_query)
            total_attempts = len(responses)
            
            avg_score = 0
            if total_attempts > 0:
                scores = [r.to_dict().get('score', 0) for r in responses]
                avg_score = sum(scores) / len(scores)
            
            with col1:
                st.metric("Total Attempts", total_attempts)
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            
            st.divider()
            st.subheader("Question Analysis")
            
            questions_query = questions_ref.where('quiz_name', '==', selected_quiz).stream()
            for q_doc in questions_query:
                q = q_doc.to_dict()
                with st.expander(f"📝 {q.get('question', 'Unknown Question')}", expanded=False):
                    votes = q.get('votes', {})
                    total_votes = sum(votes.values())
                    if total_votes > 0:
                        for opt, count in votes.items():
                            percentage = (count / total_votes) * 100
                            st.write(f"{opt}: {count} votes ({percentage:.1f}%)")
                            st.progress(percentage / 100)
                            if opt == q.get('correct'):
                                st.success("✅ Correct Answer")
                    else:
                        st.info("No responses yet")
            
            st.divider()
            st.subheader("📈 Leaderboard")
            
            responses_query = responses_ref.where('quiz', '==', selected_quiz).stream()
            responses_data = [r.to_dict() for r in responses_query]
            
            leaderboard = {}
            for r in responses_data:
                username = r.get('user', 'Unknown User')
                score = r.get('score', 0)
                if username not in leaderboard:
                    leaderboard[username] = {'best_score': score, 'attempts': 1}
                else:
                    leaderboard[username]['attempts'] += 1
                    leaderboard[username]['best_score'] = max(leaderboard[username]['best_score'], score)
            
            sorted_leaders = sorted(leaderboard.items(), key=lambda x: x[1]['best_score'], reverse=True)[:10]
            
            for idx, (username, data) in enumerate(sorted_leaders):
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    st.write(f"{idx + 1}. {username}")
                with col2:
                    st.write(f"{data['best_score']:.1f}%")
                with col3:
                    st.write(f"{data['attempts']} attempts")
    
    except Exception as e:
        st.error(f"An error occurred while loading the results: {str(e)}")
        print(f"Error in view_results: {str(e)}")  # For debugging

def sidebar_nav():
    st.sidebar.title("Navigation")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    if "user" not in st.session_state:
        auth_choice = st.sidebar.radio("Select Option", ["Login", "Sign Up"])
        if auth_choice == "Login":
            login()
        else:
            signup()
    else:
        st.sidebar.write(f"Welcome, {st.session_state['user']['username']}!")
        role = st.session_state["user"]["role"]
        
        if role == "admin":
            page = st.sidebar.radio("Go to", ["Make Quiz", "Results"])
            if page == "Make Quiz":
                admin_panel()
            elif page == "Results":
                view_results()
        else:
            if "quiz_started" in st.session_state and st.session_state["quiz_started"]:
                play_quiz()
            else:
                available_quizzes()

def main():
    sidebar_nav()

if __name__ == "__main__":
    main()