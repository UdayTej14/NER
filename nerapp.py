import streamlit as st
import spacy
import PyPDF2
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"


st.set_page_config(
    page_title="NER",
    page_icon="🔍",
    initial_sidebar_state="collapsed",
)

# Function to load the pre-trained NER model
def load_model():
    return spacy.load("en_core_web_sm")

# Function to process the input text with the loaded model
def process_text(model, input_text):
    doc = model(input_text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader=PdfReader(file)
    page=reader.pages[0]
    text=page.extract_text()
    return text

# Function to extract text from Word document
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to extract text from image using OCR
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

# Function to count the words in the text
def word_count(text):
    words = text.split()
    return len(words)

def main():
    st.title("Named Entity Recognition")

    # Load the pre-trained NER model
    model = load_model()

    # Initialize history using Streamlit session state
    if "history" not in st.session_state:
        st.session_state.history = []
    
    uploaded_file = st.file_uploader("Upload PDF, Word Document, or Image", type=["pdf", "docx", "jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Check file type and extract text accordingly
        if uploaded_file.type == "application/pdf":
            text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(uploaded_file)
        elif uploaded_file.type.startswith("image"):
            image = Image.open(uploaded_file)
            text = extract_text_from_image(image)
        else:
            st.error("Unsupported file format. Please upload a PDF, Word document, or image.")
            return

        # Display extracted text
        st.subheader("Document Text:")
        st.write(text)

        # Button to trigger the NER processing
        if st.button("Process Document"):
            # Process the extracted text
            entities = process_text(model, text)
            
            # Append input and output to history
            st.session_state.history.append(("Uploaded Document", entities))

            # Display the output
            st.subheader("Entities found:")
            if entities:
                for entity, label in entities:
                    st.write(f"- {entity} ({label})")
            else:
                st.write("No entities found.")
    
    # Input text area
    input_text = st.text_area("Enter your text here:", "")

    # Check word count
    num_words = word_count(input_text)
    st.write(f"Word count: {num_words}/1000")

    # Button to trigger the NER processing
    if st.button("Process Text"):
        if input_text.strip() != "":
            if num_words > 1000:
                st.error("Word limit exceeded! Please shorten your text to 1000 words or less.")
            else:
                # Process the input text
                entities = process_text(model, input_text)
                
                # Append input and output to history
                st.session_state.history.append((input_text, entities))
                
                # Display the output
                st.subheader("Entities found:")
                if entities:
                    for entity, label in entities:
                        st.write(f"- {entity} ({label})")
                else:
                    st.write("No entities found.")
        else:
            st.write("Please enter some text to process.")
    
    # Sidebar for history
    with st.sidebar:
        st.title("History")
        if st.session_state.history:
            for i, (text, entities) in enumerate(st.session_state.history):
                with st.expander(f"Input {i+1}", expanded=False):
                    st.write(text)
                    if entities:
                        for entity, label in entities:
                            st.write(f"- {entity} ({label})")
                    else:
                        st.write("No entities found.")
        else:
            st.write("No history yet.")

if __name__ == "__main__":
    main()
