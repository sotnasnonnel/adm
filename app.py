import streamlit as st
import fitz  # PyMuPDF
import re
import os
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import zipfile

# Função para extrair nome de uma página do PDF
def extract_name_from_page(page_text):
    match = re.search(r'NOME COMPLETO\s*([\w\s]+)', page_text)
    if match:
        return match.group(1).strip()
    return None

# Função para dividir PDF por páginas e renomear pelos nomes
def split_pdf_by_pages_clt(input_pdf, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(input_pdf)
    num_pages = len(reader.pages)
    
    saved_files = []
    for i in range(num_pages):
        page = reader.pages[i]
        text = page.extract_text()
        name = extract_name_from_page(text)
        
        if name:
            output_pdf_path = os.path.join(output_dir, f"{name}.pdf")
            writer = PdfWriter()
            writer.add_page(page)
            
            with open(output_pdf_path, 'wb') as output_pdf_file:
                writer.write(output_pdf_file)
            saved_files.append(output_pdf_path)
        else:
            st.warning(f"Nome não encontrado na página {i + 1}")
    
    return saved_files

# Função para extrair nomes dos colaboradores
def extract_employee_names_with_refined_cbo(pdf_path):
    names = []
    document = fitz.open(pdf_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'\b\d{6}\b', line):  # Pattern to match CBO code (6 digits)
                for j in range(i - 3, i):
                    if j >= 0:
                        name_line = lines[j].strip()
                        if name_line and not any(keyword in name_line for keyword in ["Nome do Funcionário", "Departamento", "Filial", "Mensalista", "Admissão", "Folha Mensal"]) and not name_line.isdigit():
                            names.append(name_line)
                            break
                break

    return names

# Função para dividir PDF por páginas e renomear pelos nomes
def split_pdf_by_pages_colaborador(uploaded_file, output_dir):
    input_pdf_path = "uploaded_file.pdf"
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())
    
    employee_names = extract_employee_names_with_refined_cbo(input_pdf_path)
    
    saved_files = []
    document = fitz.open(input_pdf_path)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for page_num, name in enumerate(employee_names):
        writer = PdfWriter()
        page = document.load_page(page_num)
        single_page_pdf = fitz.open()
        single_page_pdf.insert_pdf(document, from_page=page_num, to_page=page_num)
        pdf_bytes = single_page_pdf.tobytes()
        pdf_bytes_io = BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_bytes_io)
        writer.add_page(pdf_reader.pages[0])

        output_path = os.path.join(output_dir, f"{name}.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
            saved_files.append(output_path)
    
    return saved_files

# Função para criar um arquivo zip de vários arquivos
def create_zip_file(file_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    return zip_buffer

# Função principal
def main():
    st.title("Dividir PDF por Páginas e Renomear pelos Nomes")
    
    page = st.sidebar.selectbox("Selecione a página", ["Colaborador", "CLT"])
    
    uploaded_file = st.file_uploader("Carregue um arquivo PDF", type="pdf")
    output_dir = "output"  # Diretório temporário para salvar os arquivos

    if uploaded_file is not None:
        if page == "Colaborador":
            if st.button("Processar PDF"):
                with st.spinner("Processando..."):
                    saved_files = split_pdf_by_pages_clt(uploaded_file, output_dir)
                st.success("Processamento completo!")
                st.write("Arquivos salvos:")
                zip_buffer = create_zip_file(saved_files)
                st.download_button(label="Baixar todos os PDFs", data=zip_buffer, file_name="pdfs.zip", mime="application/zip")
        elif page == "CLT":
            if st.button("Processar PDF"):
                with st.spinner("Processando..."):
                    saved_files = split_pdf_by_pages_colaborador(uploaded_file, output_dir)
                st.success("Processamento completo!")
                st.write("Arquivos salvos:")
                zip_buffer = create_zip_file(saved_files)
                st.download_button(label="Baixar todos os PDFs", data=zip_buffer, file_name="pdfs.zip", mime="application/zip")

if __name__ == "__main__":
    main()
