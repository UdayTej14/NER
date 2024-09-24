import streamlit as st
import spacy
import PyPDF2
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import utils
from io import BytesIO
import textwrap

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

# Utility to wrap text to fit within the page width
def wrap_text(c, text, x, y, max_width):
    wrapped_text = textwrap.wrap(text, width=max_width)
    for line in wrapped_text:
        if y < 40:  # If close to the bottom of the page, create a new page
            c.showPage()
            y = 750  # Reset y position
        c.drawString(x, y, line)
        y -= 12  # Move to the next line
    return y

# Function to create PDF log with text wrapping and pagination
def create_pdf_log(input_text, entities):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40  # Left margin
    y = 750  # Starting height from the top

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Named Entity Recognition Log")
    y -= 30

    # Input Text
    c.setFont("Helvetica", 12)
    c.drawString(x, y, "Input Text:")
    y -= 20

    y = wrap_text(c, input_text, x, y, 90)  # Wrap input text and update y-position

    # Entities Found
    y -= 20  # Add some space between input and entities
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Entities found:")
    y -= 20

    # Wrap entity text
    c.setFont("Helvetica", 12)
    if entities:
        for entity, label in entities:
            y = wrap_text(c, f"- {entity} ({label})", x, y, 90)
    else:
        y = wrap_text(c, "No entities found.", x, y, 90)

    c.save()
    buffer.seek(0)  # Move to the start of the file buffer

    return buffer

# Function to create a PDF for the entire history of logs
def create_pdf_history_log(history):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40  # Left margin
    y = 750  # Starting height from the top

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Complete History Log")
    y -= 30

    for i, (input_text, entities) in enumerate(history):
        if y < 100:  # Add a new page if reaching the bottom
            c.showPage()
            y = 750
        
        # Add input text
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, f"Entry {i+1} - Input Text:")
        y -= 20
        c.setFont("Helvetica", 12)
        y = wrap_text(c, input_text, x, y, 90)

        # Add entities found
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "Entities found:")
        y -= 20
        c.setFont("Helvetica", 12)
        if entities:
            for entity, label in entities:
                y = wrap_text(c, f"- {entity} ({label})", x, y, 90)
        else:
            y = wrap_text(c, "No entities found.", x, y, 90)

        y -= 40  # Add some space between entries

    c.save()
    buffer.seek(0)
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
            
            #
