import streamlit as st
import base64

# --- Helper function for base64 image (Frutiger Aero aesthetic) ---
# Assuming you save the provided image as 'aero_mockup.png'
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Ensure you have the image 'aero_mockup.png' in the same directory.
try:
    aero_bg_base64 = get_base64_of_bin_file('aero_mockup.png')
except FileNotFoundError:
    # Fallback in case image is missing during development
    aero_bg_base64 = ""
    st.warning("Could not find 'aero_mockup.png'. Frutiger Aero aesthetic may be limited.")

# --- 1. ENHANCED FRUTIGER AERO DESIGN CSS ---
# Injecting CSS for a refined look inspired by the provided mock-up
st.markdown(f"""
<style>
/* 2000s Gradient Background & Aero Image Layer */
.stApp {{
    background-color: #a1c4fd; /* Fallback */
    background-image: 
        url("data:image/png;base64,{aero_bg_base64}"), 
        linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%);
    background-size: cover;
    background-position: center;
    background-blend-mode: overlay; /* Blends the image with the gradient */
    font-family: "Trebuchet MS", sans-serif;
}}

/* Glossy Chat Container & Bubbles */
.stChatContainer, [data-testid="stChatMessageContainer"] {{
    background: rgba(255, 255, 255, 0.4) !important;
    border-radius: 30px;
    padding: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    margin-bottom: 20px;
}}

.stChatMessage {{
    border-radius: 25px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1), inset 0 2px 5px rgba(255, 255, 255, 1);
    margin-bottom: 10px;
    color: #02507d !important;
}}

.stChatMessage.user {{
    background: linear-gradient(180deg, #e0f7fa 0%, #b2ebf2 100%);
}}

.stChatMessage.assistant {{
    background: linear-gradient(180deg, #ffffff 0%, #e1f5fe 100%);
}}

/* Layout for Input and Attach Button */
[data-testid="column"] {{
    display: flex;
    align-items: center;
}}

/* Quirky Aero Title */
h1#chatbot-aero {{
    color: #02507d;
    text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8);
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)

# Show title and description.
st.title("🫧 Chatbot Aero", anchor="chatbot-aero")
st.write(
    "Welcome to the **AeroChat** interface! 🐬 Upload PDFs and start prompting directly below."
)

st.divider()

# Organize the chat window area
chat_container = st.container()

# Organize the input and attach area
input_and_attach_container = st.container()

st.divider()

# Organize the file upload area separately, below the divider
upload_container = st.container()


# Initialize state for chat history and document context
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_doc_text" not in st.session_state:
    st.session_state.processed_doc_text = ""

# --- CHAT INPUT AREA (Layout) ---
# Use columns inside input_and_attach_container to align input and button
with input_and_attach_container:
    input_col, attach_col = st.columns([7, 1])  # Dynamic sizing

    # `accept_file=None` here because we use a standalone uploader
    prompt = input_col.chat_input("What is up?")

    # Standalone 'Attach' button using st.button
    # This design requires users to upload the file first via the uploader below
    attach_button = attach_col.button("📎 Attach")


# --- DOCUMENT UPLOAD AREA (Functionality) ---
with upload_container:
    # Use st.file_uploader with key and 'accept_multiple_files'
    # To use a standard button for attachment, file upload must be processed separately
    uploaded_files = st.file_uploader(
        "Upload a PDF to discuss it:",
        type=["pdf"],
        accept_multiple_files=False,
        key="pdf_uploader",
        help="Upload a document, and then you can prompt the chatbot about it.",
        label_visibility="collapsed" # Hide the standard label to use our st.divider section
    )

    if uploaded_files:
        # Check if the text has already been processed to avoid re-processing on each prompt
        # We also need PyPDF2 installed for this (e.g., via pip install PyPDF2)
        try:
            import PyPDF2
        except ImportError:
            st.error("Error: The 'PyPDF2' library is not installed. Please run `pip install PyPDF2` to enable PDF reading.")
            st.stop()
            
        # Re-check to avoid reprocessing on every prompt submission.
        if uploaded_files.id != st.session_state.get('processed_doc_id'):
             # Reset current context
            st.session_state.processed_doc_text = ""

            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_files)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        st.session_state.processed_doc_text += extracted + "\n"
                st.session_state['processed_doc_id'] = uploaded_files.id # Store processed ID
                st.info(f"✅ Context from **{uploaded_files.name}** is loaded. Now you can prompt the chatbot!")
            except Exception as e:
                st.error(f"Error reading {uploaded_files.name}: {e}")


# --- CHAT & RESPONSE LOGIC ---
with chat_container:
    # Display the existing chat messages via `st.chat_message`.
    # User messages with large PDF context are trimmed for readability
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user" and "display_text" in message:
                 st.markdown(message["display_text"])
            else:
                 st.markdown(message["content"])

    # Define OpenAI key and client creation within this container if prompt received
    openai_api_key = st.secrets["openai"]["api_key"] # Access API key securely from secrets
    if prompt:
        if not openai_api_key:
             st.info("Please add your OpenAI API key to `.streamlit/secrets.toml` to continue.", icon="🗝️")
             st.stop()

        client = OpenAI(api_key=openai_api_key)

        # Retrieve the document context
        pdf_context = st.session_state.get("processed_doc_text", "")

        # Prepare user prompt and display text
        if pdf_context and uploaded_files:
            # Hide large document context from the visible chat for cleanliness
            full_user_content = f"{prompt}\n\n### Document Context ###\n{pdf_context}"
            # Custom display_text in session state to show context loaded in UI
            display_text = f"{prompt} *(uploaded context: **{uploaded_files.name}**)*"
        else:
            full_user_content = prompt
            display_text = prompt

        # Store user prompt in session state
        # Added a key 'display_text' to store the concise message for UI
        st.session_state.messages.append({"role": "user", "content": full_user_content, "display_text": display_text})
        
        # Display the prompt visually with trimmed text
        with st.chat_message("user"):
            st.markdown(display_text)

        # Generate a response using the OpenAI API.
        try:
             stream = client.chat.completions.create(
                 model="gpt-3.5-turbo",
                 messages=[
                     # Pass ONLY role and full content to API
                     {"role": m["role"], "content": m["content"]}
                     for m in st.session_state.messages
                 ],
                 stream=True,
             )

             # Stream the response to the chat using `st.write_stream`, then store it in session state.
             with st.chat_message("assistant"):
                 response = st.write_stream(stream)
             st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
             st.error(f"Error calling OpenAI API: {e}")