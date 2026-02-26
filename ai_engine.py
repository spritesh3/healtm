from openai import OpenAI
import streamlit as st

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def build_medical_prompt(patient_name, patient_history, current_message):
    return f"""
You are an AI Clinical Decision Support System (CDSS) designed for academic research.

Patient Name: {patient_name}

Previous Medical Conversation:
{patient_history}

Current Patient Message:
{current_message}

Provide response strictly in the following structured format:

1. Clinical Summary
2. Symptom Analysis
3. Differential Diagnoses (Ranked by Likelihood)
4. Risk Stratification (Low / Moderate / High)
5. Recommended Investigations
6. Suggested Next Steps
7. Medical Disclaimer

Use professional medical terminology.
Do NOT provide a definitive diagnosis.
If emergency symptoms appear, advise immediate medical attention.
"""


def ai_consult(message, username, patient_history):

    prompt = build_medical_prompt(username, patient_history, message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=700
    )

    return response.choices[0].message.content
