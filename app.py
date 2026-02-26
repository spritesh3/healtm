import streamlit as st
from database import Base, engine, SessionLocal
from models import User, Consultation, PatientMemory
from ai_engine import ai_consult
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

db = SessionLocal()

st.set_page_config(page_title="AI Telehealth System", layout="wide")

st.title("🏥 Multimodal AI Telehealth Platform")

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
        st.success("Registered")

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

    page = st.sidebar.radio("Navigation",
                             ["AI Chat", "Live Video", "Doctor Panel"])

    # ===== AI CHAT =====
    if page == "AI Chat" and user.role == "patient":

        if "chat" not in st.session_state:
            st.session_state.chat = []

        user_input = st.chat_input("Describe your symptoms...")

        if user_input:
            st.session_state.chat.append(("You", user_input))
            ai_reply = ai_consult(user_input, user.username)
            st.session_state.chat.append(("AI", ai_reply))

            db.add(Consultation(
                username=user.username,
                question=user_input,
                ai_response=ai_reply
            ))
            db.commit()

        for sender, msg in st.session_state.chat:
            with st.chat_message("assistant" if sender=="AI" else "user"):
                st.write(msg)

        memory = db.query(PatientMemory).filter(
            PatientMemory.username == user.username
        ).first()

        if memory and memory.risk_flags.lower() in ["high","emergency"]:
            st.error("🚨 High Risk Detected")

    # ===== DOCTOR PANEL =====
    if page == "Doctor Panel" and user.role == "doctor":
        patients = db.query(PatientMemory).all()
        for p in patients:
            with st.expander(p.username):
                st.write("Summary:", p.medical_summary)
                st.write("Symptoms:", p.symptoms)
                st.write("Risk:", p.risk_flags)

    # ===== VIDEO PAGE =====
    if page == "Live Video":
        from streamlit_webrtc import webrtc_streamer
        st.subheader("🎥 Live Video Consultation")
        webrtc_streamer(key="video", media_stream_constraints={
            "video": True,
            "audio": True
        })
