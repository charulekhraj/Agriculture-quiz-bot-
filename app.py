import streamlit as st
import google.generativeai as genai
import os
import json

# Initialize Gemini
api_key = os.environ.get("AIzaSyBICpoR4UWtvVfQ4H3XZOMTrICGYPNXX_Y")
genai.configure(api_key=api_key)

# Page Config
st.set_page_config(
    page_title="AgriLearn AI",
    page_icon="🌱",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background-color: #059669;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #047857;
        color: white;
    }
    .topic-card {
        padding: 20px;
        border-radius: 15px;
        background-color: white;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialization
if 'phase' not in st.session_state:
    st.session_state.phase = 'setup'
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
if 'evaluation' not in st.session_state:
    st.session_state.evaluation = None

def reset_app():
    st.session_state.phase = 'setup'
    st.session_state.questions = []
    st.session_state.current_idx = 0
    st.session_state.user_answers = []
    st.session_state.evaluation = None

# Sidebar Navigation
with st.sidebar:
    st.title("🌱 AgriLearn AI")
    st.markdown("---")
    topic = st.selectbox(
        "Focus Area",
        ["Soil Health & Nutrition", "Integrated Pest Management", "Sustainable Irrigation", "Crop Rotation & Biodiversity", "Precision Agriculture & Tech"]
    )
    difficulty = st.select_slider(
        "Difficulty Level",
        options=["Beginner", "Intermediate", "Advanced"]
    )
    st.markdown("---")
    if st.button("Restart Assessment"):
        reset_app()
        st.rerun()

# Logic: Generate Questions
def generate_questions(topic, difficulty):
    model = genai.GenerativeModel('gemini-3-flash-preview')
    prompt = f"""
    Generate 5 multiple-choice questions for a professional agricultural assessment.
    Topic: {topic}
    Level: {difficulty}
    
    Return ONLY a JSON array of objects with these keys: 
    'question' (string), 'options' (array of 4 strings), 'answer' (string matching one option), 'hint' (string).
    """
    response = model.generate_content(prompt)
    try:
        # Clean response text in case of markdown blocks
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"Failed to generate questions: {e}")
        return None

# Logic: Final Evaluation
def get_evaluation(questions, user_answers):
    model = genai.GenerativeModel('gemini-2.5-flash')
    data_summary = ""
    for i, q in enumerate(questions):
        data_summary += f"Q: {q['question']}\nUser: {user_answers[i]}\nCorrect: {q['answer']}\n\n"
    
    prompt = f"""
    As an expert agricultural scientist, provide a deep contextual evaluation of these results.
    Explain the science behind the correct answers and address potential misconceptions based on the user's choices.
    
    Data:
    {data_summary}
    
    Return your response in clean Markdown with professional headings.
    """
    response = model.generate_content(prompt)
    return response.text

# Main View Logic
if st.session_state.phase == 'setup':
    st.title("Master Modern Farming")
    st.markdown("""
    Welcome to the **AgriLearn AI** educational loop. 
    Select a topic and difficulty level in the sidebar to begin your personalized technical assessment.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**AI Tutor Ready**\nQuestions are dynamically generated to challenge your current knowledge level.")
    with col2:
        st.success("**Professional Standards**\nContent follows modern ESG and sustainable farming protocols.")

    if st.button("Initialize Assessment"):
        with st.spinner("Preparing technical curriculum..."):
            qs = generate_questions(topic, difficulty)
            if qs:
                st.session_state.questions = qs
                st.session_state.phase = 'quiz'
                st.rerun()

elif st.session_state.phase == 'quiz':
    curr = st.session_state.current_idx
    questions = st.session_state.questions
    q = questions[curr]
    
    st.caption(f"Question {curr + 1} of {len(questions)} — {topic}")
    st.progress((curr + 1) / len(questions))
    
    st.subheader(q['question'])
    
    choice = st.radio("Select the best answer:", q['options'], index=None)
    
    st.markdown(f"**Pro Tip:** *{q['hint']}*")
    
    if st.button("Submit Answer" if curr < len(questions)-1 else "Finish Assessment"):
        if choice:
            st.session_state.user_answers.append(choice)
            if curr < len(questions) - 1:
                st.session_state.current_idx += 1
                st.rerun()
            else:
                st.session_state.phase = 'results'
                st.rerun()
        else:
            st.warning("Please select an option before proceeding.")

elif st.session_state.phase == 'results':
    st.title("Assessment Analysis")
    questions = st.session_state.questions
    user_answers = st.session_state.user_answers
    
    score = 0
    for i in range(len(questions)):
        if user_answers[i] == questions[i]['answer']:
            score += 1
    
    percentage = (score / len(questions)) * 100
    
    st.metric("Expertise Score", f"{percentage}%", f"{score}/{len(questions)} Correct")
    
    if st.session_state.evaluation is None:
        with st.spinner("AI Tutor is analyzing your performance gaps..."):
            st.session_state.evaluation = get_evaluation(questions, user_answers)
            st.rerun()

    st.markdown("---")
    st.header("🔬 Deep Contextual Feedback")
    st.markdown(st.session_state.evaluation)
    
    st.markdown("---")
    st.subheader("Question Review")
    for i, q in enumerate(questions):
        with st.expander(f"Q{i+1}: {q['question'][:50]}..."):
            is_correct = user_answers[i] == q['answer']
            st.markdown(f"**Your Answer:** {user_answers[i]}")
            st.markdown(f"**Correct Answer:** {q['answer']}")
            if is_correct:
                st.success("Correct")
            else:
                st.error("Incorrect")

    if st.button("Start New Topic"):
        reset_app()
        st.rerun()
