import os
import fitz  # PyMuPDF 
from docx import Document


def extract_text_from_file(file_path: str) -> str:
    """
    Input:
        file_path: path to PDF or DOCX file

    Output:
        string containing all extracted text

    Errors:
        - FileNotFoundError if file does not exist
        - ValueError if format unsupported
        - RuntimeError if extraction fails
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError("File does not exist")

    ext = os.path.splitext(file_path)[1].lower()

    try:
        # 📕 PDF
        if ext == ".pdf":
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n\n"
            return text.strip()

        # 📘 DOCX
        elif ext == ".docx":
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)

        else:
            raise ValueError("Unsupported file format")

    except Exception as e:
        raise RuntimeError(f"Failed to extract text: {str(e)}")






##Test
if __name__ == "__main__":
    text = extract_text_from_file("jane_doe_resume4.pdf")
    print("✅ extracted text:")
    print(text[:10000]) 
