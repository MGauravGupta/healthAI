
import os
import streamlit as st
import PyPDF2
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from docx import Document

# Load API Key from .env file
load_dotenv()
if "GOOGLE_API_KEY" not in st.session_state:
    st.session_state["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", None)

if not st.session_state["GOOGLE_API_KEY"]:
    st.session_state["GOOGLE_API_KEY"] = st.text_input("Enter your Google API Key:", type="password")

if st.session_state["GOOGLE_API_KEY"]:
    genai.configure(api_key=st.session_state["GOOGLE_API_KEY"])
else:
    st.error("No API key provided. Please enter the key to proceed.")

# Load content from the updated RAG data file
def load_rag_data(docx_file):
    try:
        document = Document(docx_file)
        rag_content = ""
        for paragraph in document.paragraphs:
            rag_content += paragraph.text + "\n"
        return rag_content
    except Exception as e:
        return f"Error loading RAG data: {e}"

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        if not text.strip():
            raise ValueError("No readable text found in the PDF.")
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

# Analyze content using Generative AI
def analyze_content(text, prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(text + prompt)
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "No recommendations available for the given input."
    except Exception as e:
        return f"Error during analysis: {e}"

# Sanitize AI Response
def sanitize_response(response):
    if isinstance(response, str):
        return [item.strip() for item in response.split(",") if item.strip()]
    return []

# Single Report Analyzer Page
def report_analyzer_page():
    st.title("📄 Medical Report Analyzer")
    st.write("Upload a medical report in PDF format to analyze its content and generate tailored recommendations. 🩺")

    if not st.session_state["GOOGLE_API_KEY"]:
        st.error("API key is not configured. Please enter your API key to proceed.")
        return

    uploaded_file = st.file_uploader("📂 Upload PDF", type="pdf")

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.text_area("📜 Extracted Report Content:", pdf_text, height=300)

        abnormalities = analyze_content(pdf_text, "List all abnormalities.")
        conditions = analyze_content(pdf_text, "Identify conditions of concern.")
        medications = analyze_content(pdf_text, "Suggest medications with reasons.")
        supplements = analyze_content(pdf_text, "Recommend food supplements with benefits.")
        activities = analyze_content(pdf_text, "Suggest suitable activities with benefits.")

        st.success("✅ Analysis Complete!")
        st.markdown(f"**Abnormalities:** {abnormalities}")
        st.markdown(f"**Conditions:** {conditions}")
        st.markdown(f"**Medications:** {medications}")
        st.markdown(f"**Supplements:** {supplements}")
        st.markdown(f"**Activities:** {activities}")

# Batch Medical Report Analyzer Page
def batch_report_analyzer_page():
    st.title("📂 Batch Medical Report Analyzer")
    st.write("Upload multiple medical reports (PDF or CSV format) to analyze their content and generate collective recommendations. 🩺")

    uploaded_files = st.file_uploader("📂 Upload Files", type=["pdf", "csv"], accept_multiple_files=True)

    if uploaded_files:
        group_recommendations = {
            "common_abnormalities": set(),
            "common_conditions": set(),
            "medications": [],
            "supplements": [],
            "activities": []
        }

        for uploaded_file in uploaded_files:
            try:
                pdf_text = None

                # Handle PDF files
                if uploaded_file.name.endswith(".pdf"):
                    with st.spinner(f"🔍 Extracting text from {uploaded_file.name}..."):
                        pdf_text = extract_text_from_pdf(uploaded_file)
                        st.text_area(f"📜 Extracted Content from {uploaded_file.name}:", pdf_text, height=300)
                # Handle CSV files
                elif uploaded_file.name.endswith(".csv"):
                    with st.spinner(f"🔍 Extracting text from {uploaded_file.name}..."):
                        csv_data = pd.read_csv(uploaded_file)
                        if csv_data.empty:
                            raise ValueError("CSV file is empty.")
                        pdf_text = csv_data.to_string(index=False)
                        st.dataframe(csv_data)

                if pdf_text:
                    with st.spinner(f"🔍 Analyzing {uploaded_file.name}..."):
                        abnormalities = analyze_content(pdf_text, "List all abnormalities.")
                        conditions = analyze_content(pdf_text, "Identify conditions of concern.")
                        medications = analyze_content(pdf_text, "Suggest medications with reasons.")
                        supplements = analyze_content(pdf_text, "Recommend food supplements with benefits.")
                        activities = analyze_content(pdf_text, "Suggest suitable activities with benefits.")

                        st.markdown(f"### Results for {uploaded_file.name}")
                        st.markdown(f"**Abnormalities:** {abnormalities}")
                        st.markdown(f"**Conditions:** {conditions}")
                        st.markdown(f"**Medications:** {medications}")
                        st.markdown(f"**Supplements:** {supplements}")
                        st.markdown(f"**Activities:** {activities}")

                        group_recommendations["common_abnormalities"].update(sanitize_response(abnormalities))
                        group_recommendations["common_conditions"].update(sanitize_response(conditions))
                        group_recommendations["medications"].append(medications)
                        group_recommendations["supplements"].append(supplements)
                        group_recommendations["activities"].append(activities)

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        st.success("✅ Batch Analysis Complete!")
        st.markdown(f"### Group-Level Recommendations")
        st.markdown(f"**Common Abnormalities:** {', '.join(group_recommendations['common_abnormalities'])}")
        st.markdown(f"**Common Conditions:** {', '.join(group_recommendations['common_conditions'])}")
        st.markdown(f"**Medications:** {'; '.join(group_recommendations['medications'])}")
        st.markdown(f"**Supplements:** {'; '.join(group_recommendations['supplements'])}")
        st.markdown(f"**Activities:** {'; '.join(group_recommendations['activities'])}")

# Main App
def main():
    st.sidebar.title("🗂️ Navigation")
    choice = st.sidebar.radio(
        "Go to:",
        ["📄 Single Report Analyzer", "📂 Batch Medical Report Analyzer"]
    )

    if choice == "📄 Single Report Analyzer":
        report_analyzer_page()
    elif choice == "📂 Batch Medical Report Analyzer":
        batch_report_analyzer_page()

if __name__ == "__main__":
    main()
