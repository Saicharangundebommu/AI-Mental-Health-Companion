"""
AI Mental Health Companion
--------------------------
A Streamlit app that chats naturally, analyzes mood,
and visualizes mood trends using AI and sentiment analysis.
"""

import os
import streamlit as st
import google.generativeai as genai
from textblob import TextBlob
import pandas as pd
import random
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pyngrok import ngrok

# ---------------- CONFIGURATION ----------------
API_KEY = "AIzaSyDyvhPOdiJpMtWPlomrZxPXUmdOBUwbcCU"
NGROK_AUTH_TOKEN = "339TFfWosIeFNOVDDPiY6B5RaCg_4dCsZVZtxzf1CiPdLFEAX"

# Configure Gemini model
def configure_ai_model(api_key: str):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash-001")
    except Exception as e:
        st.error(f"Failed to configure AI model: {e}")
        st.stop()

model = configure_ai_model(API_KEY)

RELAXATION_TIPS = [
    "Take 5 deep breaths. 🌬️",
    "Try a 5-min guided meditation. 🧘",
    "Go for a short walk. 🚶",
    "Write down three things you're grateful for. ✨",
    "Listen to calming music or nature sounds. 🎶",
    "Do simple stretches to release tension. 🧎",
]

CRISIS_HELP_NUMBERS = {
    "India": "9152987821",
    "USA": "988",
    "UK": "116 123"
}

# ---------------- HELPER FUNCTIONS ----------------
def analyze_mood(text: str):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.2:
        return "Positive", polarity
    elif polarity < -0.2:
        return "Negative", polarity
    else:
        return "Neutral", polarity

def generate_ai_response(user_text: str, mood: str):
    prompt = f"""
    You are a caring and empathetic mental health companion.
    The user is feeling: {mood}.
    Provide a short, supportive response with 2-3 practical tips
    or coping strategies tailored to the user’s mood.
    Keep it warm and encouraging.
    User said: "{user_text}"
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Sorry, I had trouble generating a response: {e}"

def append_crisis_or_tip(reply: str, polarity: float):
    if polarity < -0.6:
        reply += "\n\n> 🚨 **Important:** You seem to be struggling. Consider reaching out to a crisis support line. "
        reply += "In India: {India}, USA: {USA}, UK: {UK}".format(**CRISIS_HELP_NUMBERS)
    elif polarity < -0.2:
        reply += f"\n\n> 💡 **Tip:** {random.choice(RELAXATION_TIPS)}"
    return reply

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="AI Mental Health Companion", page_icon="💬", layout="centered")

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { padding: 12px; border-radius: 12px; margin-bottom: 5px; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("ℹ️ About")
    st.info("AI Mental Health Companion — chat naturally and get mood insights. **Not a substitute for medical advice.**")
    st.title("🌿 Relaxation Tips")
    for tip in RELAXATION_TIPS:
        st.markdown(f"- {tip}")
    with st.expander("📞 Crisis Support Numbers"):
        for country, number in CRISIS_HELP_NUMBERS.items():
            st.markdown(f"- **{country}:** {number}")

# Main chat interface
st.title("💬 Mental Health Companion")
st.markdown("Chat with your AI friend. Mood insights will appear after a few messages.")
st.divider()

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "content": "Hello! I'm here to listen. How are you feeling today?"}]
if "mood_log" not in st.session_state:
    st.session_state.mood_log = []
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "suggestion_active" not in st.session_state:
    st.session_state.suggestion_active = False

# Display chat messages with color coding
for msg in st.session_state.history:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        mood, _ = analyze_mood(content)
        bg_color = "#2ecc71" if mood=="Positive" else "#e74c3c" if mood=="Negative" else "#f1c40f"
    else:
        bg_color = "#34495e"
    st.markdown(f"""
    <div style="background-color:{bg_color}; color:white; padding:12px; border-radius:10px; margin-bottom:5px;">
        <b>{'Assistant 🤖' if role=='assistant' else 'You 🧑'}:</b> {content}
    </div>
    """, unsafe_allow_html=True)

# Chat input
if user_input := st.chat_input("Type your message..."):
    st.session_state.user_message_count += 1
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        mood, polarity = analyze_mood(user_input)
        reply = generate_ai_response(user_input, mood)

        if st.session_state.user_message_count >= 2:
            st.session_state.suggestion_active = True
            reply = append_crisis_or_tip(reply, polarity)

        if st.session_state.suggestion_active:
            st.session_state.mood_log.append({
                "time": datetime.datetime.now(),
                "mood": mood,
                "score": polarity,
                "entry": user_input
            })

        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})

# Enhanced Mood Dashboard
if st.session_state.suggestion_active and st.session_state.mood_log:
    st.divider()
    st.header("📊 Enhanced Mood Dashboard")
    df = pd.DataFrame(st.session_state.mood_log)
    df['time'] = pd.to_datetime(df['time'])
    df['day'] = df['time'].dt.date

    # Mood Distribution Pie
    st.subheader("Mood Distribution")
    mood_counts = df['mood'].value_counts()
    fig, ax = plt.subplots(figsize=(4,4))
    ax.pie(mood_counts, labels=mood_counts.index, autopct='%1.1f%%', startangle=90,
           colors=["#2ecc71","#f1c40f","#e74c3c"])
    ax.axis('equal')
    st.pyplot(fig)

    # Mood Timeline
    st.subheader("Mood Timeline")
    fig2, ax2 = plt.subplots(figsize=(6,3))
    sns.lineplot(data=df, x='time', y='score', marker='o', ax=ax2)
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Mood Polarity Score")
    st.pyplot(fig2)

    # Daily Summary
    st.subheader("📅 Daily Mood Summary")
    daily_summary = df.groupby('day')['score'].mean().reset_index()
    st.dataframe(daily_summary, use_container_width=True)

    # Last 5 Tips
    st.subheader("💡 Recent Suggested Relaxation Tips")
    tips_used = [append_crisis_or_tip(msg['entry'], msg['score']) for msg in st.session_state.mood_log]
    for tip in tips_used[-5:]:
        st.markdown(f"- {tip.split('💡 **Tip:**')[-1].strip()}")

