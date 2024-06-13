import streamlit as st
import fitz  # PyMuPDF
import re
import os
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO

def extract_employee_names_with_refined_cbo(pdf_path):
    names = []
    document = fitz.open(pdf_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")

        # Split the text into lines and look for the employee name by finding the CBO line
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'\b\d{6}\b', line):  # Pattern to match CBO code (6 digits)
                # Extract the name from a few lines before the CBO line
                for j in range(i - 3, i):
                    if j >= 0:
                        name_line = lines[j].strip()
                        if name_line and not any(keyword in name_line for keyword in ["Nome do Funcionário", "Departamento", "Filial", "Mensalista", "Admissão", "Folha Mensal"]) and not name_line.isdigit():
                            names.append(name_line)
                            break
                break  # Go to the next page after finding the name

    return names

def split_pdf_by_pages(uploaded_file, output_dir):
    # Save the uploaded file temporarily
    input_pdf_path = "uploaded_file.pdf"
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())
    
    # Extract employee names
    employee_names = extract_employee_names_with_refined_cbo(input_pdf_path)
    
    saved_files = []
    document = fitz.open(input_pdf_path)
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for page_num, name in enumerate(employee_names):
        writer = PdfWriter()
        page = document.load_page(page_num)
        
        # Create a new PDF in memory with the single page
        single_page_pdf = fitz.open()  # Create a new empty PDF
        single_page_pdf.insert_pdf(document, from_page=page_num, to_page=page_num)
        
        # Convert the single page PDF to bytes
        pdf_bytes = single_page_pdf.tobytes()
        pdf_bytes_io = BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_bytes_io)
        
        writer.add_page(pdf_reader.pages[0])

        output_path = os.path.join(output_dir, f"{name}.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
            saved_files.append(output_path)
    
    return saved_files

def main():
    st.title("Dividir PDF por Páginas e Renomear pelos Nomes")
    
    uploaded_file = st.file_uploader("Carregue um arquivo PDF", type="pdf")
    
    if uploaded_file is not None:
        output_dir = "clt"
        
        if st.button("Processar PDF"):
            with st.spinner("Processando..."):
                saved_files = split_pdf_by_pages(uploaded_file, output_dir)
            
            st.success("Processamento completo!")
            st.write("Arquivos salvos:")
            for file in saved_files:
                st.write(file)

if __name__ == "__main__":
    main()
