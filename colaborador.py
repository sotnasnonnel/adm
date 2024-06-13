import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import re
import os

def extract_name_from_page(page_text):
    match = re.search(r'NOME COMPLETO\s*([\w\s]+)', page_text)
    if match:
        return match.group(1).strip()
    return None

def split_pdf_by_pages(input_pdf, output_dir):
    # Certifique-se de que o diretório de saída existe
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

def main():
    st.title("Dividir PDF por Páginas e Renomear pelos Nomes")
    
    uploaded_file = st.file_uploader("Carregue um arquivo PDF", type="pdf")
    
    if uploaded_file is not None:
        output_dir = "colaboradores"
        
        if st.button("Processar PDF"):
            with st.spinner("Processando..."):
                saved_files = split_pdf_by_pages(uploaded_file, output_dir)
            
            st.success("Processamento completo!")
            st.write("Arquivos salvos:")
            for file in saved_files:
                st.write(file)

if __name__ == "__main__":
    main()
