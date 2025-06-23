import streamlit as st
import requests
import string

API_URL = "https://guess-ai-backend.onrender.com/generate-quiz"

def generate_quiz(topic: str):
    resp = requests.post(API_URL, json={"topic": topic})
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────────────────────────────────────
# Session‐state initialization
# ─────────────────────────────────────────────────────────────────────────────
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "quiz_items" not in st.session_state:
    st.session_state.quiz_items = []
if "filled" not in st.session_state:
    st.session_state.filled = []

st.title("🔍 Guess.ai Quiz")

# ─────────────────────────────────────────────────────────────────────────────
# 1) Topic input + Generate Quiz
# ─────────────────────────────────────────────────────────────────────────────
topic = st.text_input(
    "Make me a quiz about…",
    value=st.session_state.current_topic,
    key="topic_input"
)
if st.button("Generate Quiz"):
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        data = generate_quiz(topic.strip())
        if data.get("quiz_type") != "list":
            st.error("Sorry—this demo only handles list‐type quizzes.")
        else:
            # store new quiz
            st.session_state.current_topic = topic.strip()
            st.session_state.quiz_items = data["items"]
            st.session_state.filled = [""] * len(data["items"])

# ─────────────────────────────────────────────────────────────────────────────
# 2) If we have a quiz, show the guess form + grid
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.quiz_items:
    st.markdown("---")
    st.subheader("Try to guess an item:")

    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Your guess")
        submitted = st.form_submit_button("Submit Guess")
        if submitted:
            g_normal = guess.strip().lower().strip(string.punctuation)
            found = False
            for i, item in enumerate(st.session_state.quiz_items):
                # normalize the stored item too
                item_norm = item.lower().strip(string.punctuation)
                if item_norm == g_normal and not st.session_state.filled[i]:
                    st.success(f"✅ Correct: {item}")
                    st.session_state.filled[i] = item
                    found = True
                    break
            if not found:
                st.warning("❌ Nope—that’s not on this quiz.")

    # ─────────────────────────────────────────────────────────────────────────
    # 3) Render the boxes in a responsive grid
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Your Quiz Items")
    count = len(st.session_state.quiz_items)
    cols = st.columns(min(4, count))  # up to 4 columns
    for idx, item in enumerate(st.session_state.quiz_items):
        col = cols[idx % len(cols)]
        content = st.session_state.filled[idx] or ""
        col.markdown(
            f"""
            <div style="
              border: 2px solid #444;
              border-radius: 8px;
              padding: 12px;
              min-height: 60px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-weight: 600;
            ">
              {content}
            </div>
            """,
            unsafe_allow_html=True,
        )

