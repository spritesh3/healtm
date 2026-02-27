import streamlit as st
from database import Base, engine, SessionLocal
from models import User, Consultation, PatientMemory
from ai_engine import ai_consult
from sqlalchemy.orm import Session
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile

Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="AI Telehealth System", layout="wide")
st.title("🏥 Multimodal AI Telehealth Platform")

db = SessionLocal()

# ================= AUTH =================

if "user" not in st.session_state:
    st.session_state.user = None

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

# -------- REGISTER --------
if choice == "Register":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["patient", "doctor"])

    if st.button("Register"):
        try:
            db.add(User(username=username, password=password, role=role))
            db.commit()
            st.success("Registered Successfully")
        except Exception as e:
            db.rollback()
            st.error(f"Registration failed: {e}")

# -------- LOGIN --------
if choice == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = db.query(User).filter(
            User.username == username,
            User.password == password
        ).first()

        if user:
            st.session_state.user = user
        else:
            st.error("Invalid credentials")

# ================= DASHBOARD =================

if st.session_state.user:

    user = st.session_state.user

    page = st.sidebar.radio(
        "Navigation",
        ["AI Chat", "Live Video", "Doctor Panel"]
    )

    # ================= AI CHAT =================
    if page == "AI Chat" and user.role == "patient":

        st.subheader("🤖 Multilingual AI Clinical Assistant")

        if "chat" not in st.session_state:
            st.session_state.chat = []

        # -------- LOAD HISTORY --------
        consultations = db.query(Consultation).filter(
            Consultation.username == user.username
        ).all()

        history_text = ""
        for c in consultations:
            history_text += f"Patient: {c.question}\nAI: {c.ai_response}\n"

        if not history_text:
            history_text = "No previous history."

        # ================= VOICE INPUT =================
        st.markdown("### 🎤 Speak or Type Your Symptoms")

        audio = mic_recorder(
            start_prompt="🎙 Start Recording",
            stop_prompt="⏹ Stop Recording",
            key="recorder"
        )

        user_input = None

        # Voice input
        if audio and audio["text"]:
            user_input = audio["text"]
            st.info(f"You said: {user_input}")

        # Text input fallback
        text_input = st.chat_input("Or type your symptoms here...")
        if text_input:
            user_input = text_input

        # ================= AI PROCESS =================
        if user_input:

            st.session_state.chat.append(("You", user_input))

            ai_reply = ai_consult(user_input, user.username, history_text)

            st.session_state.chat.append(("AI", ai_reply))

            # Save consultation safely
            try:
                db.add(Consultation(
                    username=user.username,
                    question=user_input,
                    ai_response=ai_reply
                ))
                db.commit()
            except:
                db.rollback()

            # -------- UPDATE MEMORY --------
            memory = db.query(PatientMemory).filter(
                PatientMemory.username == user.username
            ).first()

            if not memory:
                memory = PatientMemory(
                    username=user.username,
                    medical_summary="",
                    symptoms="",
                    risk_flags="Low"
                )
                db.add(memory)

            memory.medical_summary = ai_reply
            memory.symptoms = user_input

            if "High" in ai_reply or "Emergency" in ai_reply:
                memory.risk_flags = "High"
            elif "Moderate" in ai_reply:
                memory.risk_flags = "Moderate"
            else:
                memory.risk_flags = "Low"

            db.commit()

            # ================= VOICE RESPONSE =================
            try:
                tts = gTTS(ai_reply)
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_audio.name)
                st.audio(temp_audio.name)
            except:
                pass

        # -------- DISPLAY CHAT --------
        for sender, msg in st.session_state.chat:
            with st.chat_message("assistant" if sender == "AI" else "user"):
                st.write(msg)

        # -------- RISK ALERT --------
        memory = db.query(PatientMemory).filter(
            PatientMemory.username == user.username
        ).first()

        if memory and memory.risk_flags.lower() in ["high", "emergency"]:
            st.error("🚨 High Risk Detected — Seek Immediate Medical Care")

    # ================= DOCTOR PANEL =================
    if page == "Doctor Panel" and user.role == "doctor":

        st.subheader("👨‍⚕ Doctor Dashboard")

        patients = db.query(PatientMemory).all()

        for p in patients:
            with st.expander(f"Patient: {p.username}"):

                st.write("### 📝 Medical Summary")
                st.write(p.medical_summary)

                st.write("### 🤒 Latest Symptoms")
                st.write(p.symptoms)

                st.write("### ⚠ Risk Level")

                if p.risk_flags.lower() == "high":
                    st.error(p.risk_flags)
                elif p.risk_flags.lower() == "moderate":
                    st.warning(p.risk_flags)
                else:
                    st.success(p.risk_flags)

    # ================= VIDEO PAGE =================
    if page == "Live Video":

        from streamlit_webrtc import webrtc_streamer

        st.subheader("🎥 Live Video Consultation")

        webrtc_streamer(
            key="video",
            media_stream_constraints={
                "video": True,
                "audio": True
            }
        )
