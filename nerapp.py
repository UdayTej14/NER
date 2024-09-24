import streamlit as st
import spacy
import PyPDF2
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
from reportlab.pdfgen import canvas
from io import BytesIO

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
    reader = PdfReader(file)
    page = reader.pages[0]
    text = page.extract_text()
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

# Function to create PDF log
def create_pdf_log(input_text, entities):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    
    c.drawString(100, 750, "Named Entity Recognition Log")
    c.drawString(100, 730, f"Input Text: {input_text}")
    
    c.drawString(100, 700, "Entities found:")
    y = 680
    if entities:
        for entity, label in entities:
            c.drawString(100, y, f"- {entity} ({label})")
            y -= 20
    else:
        c.drawString(100, y, "No entities found.")
    
    c.save()
    buffer.seek(0)  # Move to the start of the file buffer
    
    return buffer

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
            
            # Create PDF log and make it downloadable
            pdf_buffer = create_pdf_log(text, entities)
            st.download_button(
                label="Download Log as PDF",
                data=pdf_buffer,
                file_name="ner_log.pdf",
                mime="application/pdf"
            )
    
    # Input text area
    input_text = st.text_area("Enter your text here:", "")

    # Check word count
    num_words = word_count(input_text)
    st.write(f"Word count: {num_words}/1000")

    # Create columns for buttons side by side
    col1, col2 = st.columns([2, 1])  # Adjust the width ratio of columns if needed

    with col1:
        # Button to trigger the NER processing
        process_clicked = st.button("Process Text")

    with col2:
        # Create PDF log and make it downloadable (shown only after processing)
        if process_clicked and input_text.strip() != "" and num_words <= 1000:
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
            
            # Generate PDF and allow download
            pdf_buffer = create_pdf_log(input_text, entities)
            st.download_button(
                label="Download Log as PDF",
                data=pdf_buffer,
                file_name="ner_log.pdf",
                mime="application/pdf"
            )
        elif process_clicked and num_words > 1000:
            st.error("Word limit exceeded! Please shorten your text to 1000 words or less.")
        elif process_clicked and input_text.strip() == "":
            st.error("Please enter some text to process.")

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
