import streamlit as st
import fitz  # PyMuPDF
import re
import os
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import zipfile

# ===== util =====
NAME_AFTER_LABEL = re.compile(
    r"NOME\s+COMPLETO[:\s]*\n+([A-ZÀ-ÖØ-ÝÇÃÕÂÊÔÁÉÍÓÚÜÃÕÇ' -]{3,})",
    re.UNICODE
)

def sanitize_filename(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s{2,}', ' ', s)  # colapsa espaços
    s = re.sub(r'[\\/*?:"<>|]', '_', s)  # remove chars inválidos em filename
    return s

# ===== COLABORADOR (ajustado) =====
# Lê com PyMuPDF, acha "NOME COMPLETO" e salva cada página com o nome
def split_pdf_by_pages_colaborador(uploaded_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # salva o upload em arquivo temporário (fitz precisa de caminho/bytes)
    input_pdf_path = "uploaded_file_colaborador.pdf"
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    doc = fitz.open(input_pdf_path)
    saved_files = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")

        m = NAME_AFTER_LABEL.search(text)
        if not m:
            # fallback mais tolerante caso haja espaços/linhas extras
            m = re.search(r"NOME\s+COMPLETO.*?\n+([^\n]{3,})",
                          text, re.IGNORECASE | re.DOTALL | re.UNICODE)

        if m:
            raw_name = m.group(1).strip()
            file_name = sanitize_filename(raw_name) + ".pdf"

            # extrai a página com fitz -> bytes -> PyPDF2 (para escrever)
            single_page_pdf = fitz.open()
            single_page_pdf.insert_pdf(doc, from_page=page_num, to_page=page_num)
            pdf_bytes = single_page_pdf.tobytes()

            writer = PdfWriter()
            reader = PdfReader(BytesIO(pdf_bytes))
            writer.add_page(reader.pages[0])

            out_path = os.path.join(output_dir, file_name)
            with open(out_path, "wb") as out_f:
                writer.write(out_f)
            saved_files.append(out_path)
        else:
            st.warning(f"Nome não encontrado na página {page_num + 1}")

    return saved_files

# ===== CLT (seu que já funciona) =====
def extract_employee_names_with_refined_cbo(pdf_path):
    names = []
    document = fitz.open(pdf_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'\b\d{6}\b', line):  # CBO 6 dígitos
                for j in range(i - 3, i):
                    if j >= 0:
                        name_line = lines[j].strip()
                        if name_line and not any(keyword in name_line for keyword in [
                            "Nome do Funcionário","Departamento","Filial",
                            "Mensalista","Admissão","Folha Mensal"
                        ]) and not name_line.isdigit():
                            names.append(name_line)
                            break
                break
    return names

def split_pdf_by_pages_clt(uploaded_file, output_dir):
    input_pdf_path = "uploaded_file_clt.pdf"
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    employee_names = extract_employee_names_with_refined_cbo(input_pdf_path)
    saved_files = []
    document = fitz.open(input_pdf_path)

    os.makedirs(output_dir, exist_ok=True)

    for page_num, name in enumerate(employee_names):
        single_page_pdf = fitz.open()
        single_page_pdf.insert_pdf(document, from_page=page_num, to_page=page_num)
        pdf_bytes = single_page_pdf.tobytes()

        writer = PdfWriter()
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        writer.add_page(pdf_reader.pages[0])

        out_path = os.path.join(output_dir, f"{sanitize_filename(name)}.pdf")
        with open(out_path, "wb") as f_out:
            writer.write(f_out)
        saved_files.append(out_path)

    return saved_files

# ===== zip util =====
def create_zip_file(file_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for fp in file_paths:
            z.write(fp, os.path.basename(fp))
    zip_buffer.seek(0)
    return zip_buffer

# ===== app =====
def main():
    st.title("Dividir PDF por Páginas e Renomear pelos Nomes")

    # conforme seus rótulos:
    page = st.sidebar.selectbox("Selecione a página", ["Colaborador", "CLT"])
    uploaded_file = st.file_uploader("Carregue um arquivo PDF", type="pdf")
    output_dir = "output"

    if uploaded_file is not None:
        if page == "Colaborador":
            if st.button("Processar PDF"):
                with st.spinner("Processando..."):
                    saved = split_pdf_by_pages_colaborador(uploaded_file, output_dir)
                st.success(f"Processamento completo! {len(saved)} arquivo(s).")
                zip_buffer = create_zip_file(saved)
                st.download_button("Baixar todos os PDFs", zip_buffer, "pdfs.zip", "application/zip")
        elif page == "CLT":
            if st.button("Processar PDF"):
                with st.spinner("Processando..."):
                    saved = split_pdf_by_pages_clt(uploaded_file, output_dir)
                st.success(f"Processamento completo! {len(saved)} arquivo(s).")
                zip_buffer = create_zip_file(saved)
                st.download_button("Baixar todos os PDFs", zip_buffer, "pdfs.zip", "application/zip")

if __name__ == "__main__":
    main()
