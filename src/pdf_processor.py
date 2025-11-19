from pypdf import PdfReader

def extract_text_from_pdf(uploaded_file):
    """Lê um arquivo PDF em memória e retorna o texto bruto."""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
        return None