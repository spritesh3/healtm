from openai import OpenAI
from config import OPENAI_API_KEY
from models import PatientMemory
from database import SessionLocal
from datetime import datetime

client = OpenAI(api_key=OPENAI_API_KEY)

def ai_consult(user_input, username):
    db = SessionLocal()

    memory = db.query(PatientMemory).filter(
        PatientMemory.username == username
    ).first()

    summary = memory.medical_summary if memory else ""
    symptoms = memory.symptoms if memory else ""

    prompt = f"""
You are an advanced clinical AI assistant.

PATIENT MEMORY:
Summary: {summary}
Symptoms: {symptoms}

New Message:
{user_input}

Tasks:
1. Analyze progression.
2. Update structured summary.
3. Update symptom list.
4. Assign risk level (Low/Moderate/High/Emergency).

Return format:

---AI RESPONSE---
Text to patient.

---UPDATED_SUMMARY---
summary

---UPDATED_SYMPTOMS---
symptoms

---RISK_FLAGS---
risk
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content

    ai_reply = content.split("---UPDATED_SUMMARY---")[0].replace("---AI RESPONSE---","").strip()
    updated_summary = content.split("---UPDATED_SUMMARY---")[1].split("---UPDATED_SYMPTOMS---")[0].strip()
    updated_symptoms = content.split("---UPDATED_SYMPTOMS---")[1].split("---RISK_FLAGS---")[0].strip()
    risk = content.split("---RISK_FLAGS---")[1].strip()

    if memory:
        memory.medical_summary = updated_summary
        memory.symptoms = updated_symptoms
        memory.risk_flags = risk
        memory.last_updated = datetime.utcnow()
    else:
        memory = PatientMemory(
            username=username,
            medical_summary=updated_summary,
            symptoms=updated_symptoms,
            risk_flags=risk
        )
        db.add(memory)

    db.commit()
    db.close()

    return ai_reply
