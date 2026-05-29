import streamlit as st
from openai import OpenAI
import PyPDF2  # Used for reading the uploaded PDF documents

# --- 1. FRUTIGER AERO DESIGN CSS ---
# Inject custom CSS for that glossy, rounded, quirky 2000s aesthetic
st.markdown("""
<style>
/* 2000s Gradient Background */
.stApp {
    background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
    font-family: "Trebuchet MS", sans-serif;
}

/* Glossy Chat Bubbles */
.stChatMessage {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.6) 0%, rgba(220, 240, 255, 0.4) 100%);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.9);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1), inset 0 3px 6px rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(8px);
    margin-bottom: 15px;
    padding: 15px;
}

/* Chat Input Bar Styling */
[data-testid="stChatInput"] {
    border-radius: 25px !important;
    background: linear-gradient(180deg, #ffffff 0%, #e6f7ff 100%) !important;
    border: 2px solid #82c8e5 !important;
    box-shadow: 0 5px 15px rgba(0, 150, 255, 0.2), inset 0 2px 5px rgba(255, 255, 255, 1) !important;
}

/* Quirky Title */
h1 {
    color: #02507d;
    text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8);
}
</style>
""", unsafe_allow_html=True)

# Show title and description.
st.title("🫧 Chatbot Aero")
st.write(
    "Welcome to the 2000s! 🐬 This chatbot uses OpenAI's GPT-3.5 model. "
    "You can now **click the paperclip icon in the chat bar** to upload PDFs for the bot to read!"
)

# Ask user for their OpenAI API key
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Display 'display_text' so we don't clog the UI with huge blocks of PDF text
            st.markdown(message.get("display_text", message["content"]))

    # --- 2. CHAT INPUT WITH PDF ATTACHMENTS ---
    # `accept_file="multiple"` adds a native paperclip icon inside the chat bar
    user_input = st.chat_input("What is up?", accept_file="multiple", file_type=["pdf"])

    if user_input:
        # Gracefully handle the chat object returned by the new file-attachment feature
        if isinstance(user_input, str):
            prompt_text = user_input
            attached_files = []
        else:
            prompt_text = getattr(user_input, "text", "")
            attached_files = getattr(user_input, "files", [])

        # Extract text from the attached PDFs
        pdf_context = ""
        if attached_files:
            for file in attached_files:
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            pdf_context += extracted + "\n"
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")
        
        # Combine the user prompt with the hidden PDF text for the LLM to read
        if pdf_context:
            full_content = f"{prompt_text}\n\n### Document Context ###\n{pdf_context}"
        else:
            full_content = prompt_text

        # Determine what text to visually show in the UI to the user
        display_text = prompt_text if prompt_text else f"*(Uploaded {len(attached_files)} document(s))*"

        # Store user prompt (We save display_text specifically for UI cleanliness)
        st.session_state.messages.append({
            "role": "user", 
            "content": full_content, 
            "display_text": display_text  
        })
        
        with st.chat_message("user"):
            st.markdown(display_text)
            if attached_files:
                st.info(f"📎 Processed {len(attached_files)} PDF(s).")

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                # Only pass the 'role' and 'content' to OpenAI (ignoring our custom 'display_text' key)
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        with st.chat_message("assistant"):
            response = st.write_stream(stream)
            
        st.session_state.messages.append({"role": "assistant", "content": response})