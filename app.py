import streamlit as st
import json
import requests

# Load buyer data
with open("buyers.json") as f:
    buyers = json.load(f)

# API Setup
API_URL = "https://api.together.xyz/v1/chat/completions"

API_KEY = st.secrets["TOGETHER_API_KEY"]
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# Buyer lookup
def find_buyer(input_value):
    for buyer in buyers:
        if buyer["name"].lower() == input_value.lower() or buyer["phone"] == input_value:
            return buyer
    return None

# System prompt
def build_system_prompt(buyer):
    prefs = buyer["preferences"]
    return f"""
You are a friendly real estate assistant. The buyer's name is {buyer['name']}. Their preferences are:
- Locations: {prefs['locations']}
- Property Type: {prefs['property_type']}
- Budget: {prefs['budget']}
- Purpose: {prefs['purpose']}
- Additional comments: {prefs['comments']}

Based on this, ask personalized, helpful, and engaging questions. Only one question at a time. Use natural, human-like tone.
"""

# Call Together API
def chat_with_llm(messages):
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300
    }
    response = requests.post(API_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Streamlit App
st.title("🏠 Real Estate Chatbot")

user_id = st.text_input("Enter your name or mobile number")
if user_id:
    buyer = find_buyer(user_id)
    if buyer:
        st.success(f"Welcome {buyer['name'].title()}! Let's talk about your property needs.")

        if "messages" not in st.session_state:
            system_prompt = build_system_prompt(buyer)
            st.session_state.messages = [{"role": "system", "content": system_prompt}]
            st.session_state.chat_history = []

            # Ask first question after trigger
            st.session_state.messages.append({"role": "user", "content": "Please begin asking questions."})
            first_question = chat_with_llm(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": first_question})
            st.session_state.chat_history.append({"role": "assistant", "content": first_question})

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Wait for user input
        if prompt := st.chat_input("Type your reply..."):
            # Add user reply
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # RENDER all history up to this point
            with st.chat_message("user"):
                st.markdown(prompt)

            # Assistant replies only after rendering
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = chat_with_llm(st.session_state.messages)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
    else:
        st.error("Buyer not found in the database.")
