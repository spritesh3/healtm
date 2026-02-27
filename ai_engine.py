import streamlit as st
from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

def ai_consult(user_input, username, history):

    structured_prompt = f"""
You are an AI Clinical Decision Support Assistant.

IMPORTANT:
- Detect the language of the patient's input.
- Respond in the SAME language.
- If input is Hindi, reply in Hindi.
- If input is Tamil, reply in Tamil.
- If input is Arabic, reply in Arabic.
- Otherwise reply in English.

Patient Name: {username}

Previous History:
{history}

New Symptoms:
{user_input}

Respond strictly in this structured format:

1. Possible Conditions:
- List top possible diagnoses

2. Risk Level:
- Low / Moderate / High

3. Recommended Action:
- Self care / Doctor visit / Emergency care

4. Brief Clinical Reasoning:
- Short explanation
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a safe multilingual medical AI assistant."},
                {"role": "user", "content": structured_prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI service temporarily unavailable: {str(e)}"
