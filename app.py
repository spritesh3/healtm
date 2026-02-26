import streamlit as st
from database import Base, engine, SessionLocal
from models import User, Consultation, PatientMemory
from ai_engine import ai_consult
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="AI Telehealth System", layout="wide")

st.title("🏥 Multimodal AI Telehealth Platform")

db = SessionLocal()

# ================= AUTH =================

if "user" not in st.session_state:
    st.session_state.user = None

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["patient", "doctor"])

    if st.button("Register"):
        db.add(User(username=username, password=password, role=role))
        db.commit()
        st.success("Registered Successfully")

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

        st.subheader("🤖 AI Clinical Assistant")

        if "chat" not in st.session_state:
            st.session_state.chat = []

        # -------- GET FULL PATIENT HISTORY --------
        consultations = db.query(Consultation).filter(
            Consultation.username == user.username
        ).all()

        history_text = ""
        for c in consultations:
            history_text += f"Patient: {c.question}\nAI: {c.ai_response}\n"

        if not history_text:
            history_text = "No previous history."

        # -------- CHAT INPUT --------
        user_input = st.chat_input("Describe your symptoms...")

        if user_input:

            st.session_state.chat.append(("You", user_input))

            # AI WITH LONGITUDINAL CONTEXT
            ai_reply = ai_consult(user_input, user.username, history_text)

            st.session_state.chat.append(("AI", ai_reply))

            # Save consultation
            db.add(Consultation(
                username=user.username,
                question=user_input,
                ai_response=ai_reply
            ))
            db.commit()

            # -------- UPDATE PATIENT MEMORY --------
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

            # Simple risk extraction logic
            if "High" in ai_reply or "Emergency" in ai_reply:
                memory.risk_flags = "High"
            elif "Moderate" in ai_reply:
                memory.risk_flags = "Moderate"
            else:
                memory.risk_flags = "Low"

            db.commit()

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
