# streamlit_app.py
import time
import requests
import streamlit as st

# ─── Configuration ─────────────────────────────────────
BACKEND_URL = "https://guess-ai-backend.onrender.com"

# ─── Site-wide CSS ─────────────────────────────────────
st.markdown(
    """
    <style>
      * { font-family: "Times New Roman", serif !important; }
      .box {
        background-color: #fff;
        border: 1px solid #ccc;
        padding: 8px;
        margin: 4px;
        min-width: 150px !important;
        max-width: 200px !important;
        min-height: 80px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        word-break: break-word;
        color: #000 !important;
      }
      .correct { background-color: #90ee90 !important; color: #000 !important; }
      .missed  { background-color: #f08080 !important; color: #000 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Guess.ai")

# ─── Initialize state ───────────────────────────────────
if "answers" not in st.session_state:
    st.session_state.answers = []
    st.session_state.guessed = set()
    st.session_state.session_id = None
    st.session_state.start_time = None
    st.session_state.give_up = False

# ─── Load a new quiz ─────────────────────────────────────
topic = st.text_input("Enter quiz topic", key="topic_input")
if st.button("Load Quiz") and topic.strip():
    try:
        r = requests.post(
            f"{BACKEND_URL}/generate-quiz",
            json={"topic": topic.strip()},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        # If backend didn’t give us a session_id or items, warn
        if not data.get("session_id") or not (
            data.get("items") or data.get("quiz")
        ):
            st.warning("Unexpected response format. Try again.")
        else:
            st.session_state.session_id = data["session_id"]
            if data["quiz_type"] == "list":
                st.session_state.answers = data["items"]
            else:
                st.session_state.answers = [
                    q["correctAnswer"] for q in data["quiz"]
                ]
            st.session_state.guessed = set()
            st.session_state.start_time = time.time()
            st.session_state.give_up = False
    except Exception as e:
        st.warning(f"Failed to load quiz: {e}")

# ─── Quiz in progress / results ─────────────────────────
if st.session_state.answers:
    st.header(f"{topic.strip().title()} Quiz")

    # elapsed timer
    elapsed = (
        int(time.time() - st.session_state.start_time)
        if st.session_state.start_time
        else 0
    )
    st.write(f"Time elapsed: {elapsed} seconds")

    # score
    total = len(st.session_state.answers)
    correct = len(st.session_state.guessed)
    percent = (correct / total * 100) if total else 0
    st.markdown(f"**Score:** {correct} / {total} ({percent:.0f}%)")

    # handle a guess
    def handle_guess():
        sid = st.session_state.session_id
        if not sid:
            return
        try:
            resp = requests.post(
                f"{BACKEND_URL}/check-guess",
                json={"session_id": sid, "guess": st.session_state.guess_input},
                timeout=5,
            )
            resp.raise_for_status()
            res = resp.json()
            if res.get("correct"):
                st.session_state.guessed.add(res.get("matched_answer"))
        except Exception:
            st.warning("Error checking your guess—please try again.")

    with st.form("guess_form", clear_on_submit=True):
        st.text_input("Your guess", key="guess_input")
        if st.form_submit_button("Guess"):
            handle_guess()

    if st.button("Give Up"):
        st.session_state.give_up = True

    # display the boxes
    num_cols = min(5, total)
    cols = st.columns(num_cols)
    for idx, ans in enumerate(st.session_state.answers):
        cls = "box"
        disp = ""
        if ans in st.session_state.guessed:
            cls += " correct"
            disp = ans
        elif st.session_state.give_up:
            cls += " missed"
            disp = ans
        cols[idx % num_cols].markdown(
            f'<div class="{cls}">{disp}</div>', unsafe_allow_html=True
        )

