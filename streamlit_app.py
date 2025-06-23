# streamlit_app.py
import time
import requests
import streamlit as st

# ─── Site-wide CSS (Times New Roman + uniform boxes + wrap + black text) ───
st.markdown(
    """
    <style>
      * {
        font-family: "Times New Roman", serif !important;
      }
      .box {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        padding: 8px;
        margin: 4px 0;
        width: 100%;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        white-space: normal !important;
        word-break: break-word;
        color: #000000 !important;
      }
      .correct {
        background-color: #90ee90 !important;
        color: #000000 !important;
      }
      .missed {
        background-color: #f08080 !important;
        color: #000000 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Guess.ai")

# --- Load a new quiz ---
topic = st.text_input("Enter quiz topic")
if st.button("Load Quiz"):
    if topic.strip():
        resp = requests.post(
            "http://127.0.0.1:8000/generate-quiz",
            json={"topic": topic.strip()},
        )
        resp.raise_for_status()
        st.session_state.answers = resp.json().get("items", [])
        st.session_state.guessed = set()
        st.session_state.start_time = time.time()
        st.session_state.give_up = False

# --- Quiz in progress / results ---
if "answers" in st.session_state:
    st.header(f"{topic.strip().title()} Quiz")

    # show elapsed time
    elapsed = int(time.time() - st.session_state.start_time)
    st.write(f"Time elapsed: {elapsed} seconds")

    # handle a guess
    def handle_guess():
        guess = st.session_state.guess_input.strip().lower()
        for ans in st.session_state.answers:
            if guess == ans.lower():
                st.session_state.guessed.add(ans)
                break

    # replace input + button with a form so Enter submits
    with st.form("guess_form", clear_on_submit=True):
        st.text_input("Your guess", key="guess_input")
        submitted = st.form_submit_button("Guess")
        if submitted:
            handle_guess()

    if st.button("Give Up"):
        st.session_state.give_up = True

    # display answer boxes in an 8-column grid
    cols = st.columns(8)
    for idx, ans in enumerate(st.session_state.answers):
        cls = "box"
        disp = ""
        if ans in st.session_state.guessed:
            cls += " correct"
            disp = ans
        elif st.session_state.give_up:
            cls += " missed"
            disp = ans
        cols[idx % 8].markdown(f'<div class="{cls}">{disp}</div>', unsafe_allow_html=True)

