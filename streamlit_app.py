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
        background-color: #ffffff;
        border: 1px solid #cccccc;
        padding: 8px;
        margin: 4px;
        min-width: 150px !important;
        max-width: 200px !important;
        min-height: 80px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        word-break: break-word;
        color: #000000 !important;
      }
      .correct { background-color: #90ee90 !important; color: #000000 !important; }
      .missed  { background-color: #f08080 !important; color: #000000 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Guess.ai")

# ─── Load a new quiz ─────────────────────────────────────
topic = st.text_input("Enter quiz topic")

if st.button("Load Quiz") and topic.strip():
    try:
        resp = requests.post(
            f"{BACKEND_URL}/generate-quiz",
            json={"topic": topic.strip()},
            timeout=10,
        )
    except Exception as e:
        st.error(f"🚨 Network error: {e}")
        # skip the rest of the block
    else:
        if resp.status_code != 200:
            st.error(f"🚨 Backend error {resp.status_code}")
            st.text(resp.text)
        else:
            try:
                data = resp.json()
            except ValueError:
                st.error("🚨 Invalid JSON from backend")
                st.text(resp.text)
            else:
                if "session_id" not in data:
                    st.error("🚨 Missing `session_id` in response")
                    st.json(data)
                else:
                    # stash session_id + answers
                    st.session_state.session_id = data["session_id"]
                    if data.get("quiz_type") == "list":
                        st.session_state.answers = data.get("items", [])
                    else:
                        st.session_state.answers = [
                            q.get("correctAnswer") for q in data.get("quiz", [])
                        ]
                    st.session_state.guessed = set()
                    st.session_state.start_time = time.time()
                    st.session_state.give_up = False

# ─── Quiz in progress / results ─────────────────────────
if "answers" in st.session_state:
    st.header(f"{topic.strip().title()} Quiz")

    # elapsed time
    elapsed = int(time.time() - st.session_state.start_time)
    st.write(f"Time elapsed: {elapsed} seconds")

    # score display
    total = len(st.session_state.answers)
    correct = len(st.session_state.guessed)
    percent = (correct / total) * 100 if total else 0
    st.markdown(f"**Score:** {correct} / {total} ({percent:.0f} %)")

    # handle a guess
    def handle_guess():
        try:
            r = requests.post(
                f"{BACKEND_URL}/check-guess",
                json={
                    "session_id": st.session_state.session_id,
                    "guess": st.session_state.guess_input,
                },
                timeout=5,
            )
            if r.status_code == 200:
                res = r.json()
                if res.get("correct"):
                    st.session_state.guessed.add(res.get("matched_answer"))
            else:
                st.warning(f"⚠️ check-guess returned {r.status_code}")
        except Exception as e:
            st.error(f"🚨 Guess error: {e}")

    with st.form("guess_form", clear_on_submit=True):
        st.text_input("Your guess", key="guess_input")
        if st.form_submit_button("Guess"):
            handle_guess()

    if st.button("Give Up"):
        st.session_state.give_up = True

    # display answers
    num_cols = min(5, len(st.session_state.answers))
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

