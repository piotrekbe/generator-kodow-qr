import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile

def generate_pdf(label, code):
    pdf = FPDF(unit="mm", format=(100, 100)) # Mały format PDF
    pdf.add_page()
    
    # Ustawienie czcionki dla wartości (np. 50 PLN)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, label, ln=True, align='C')
    
    # Generowanie kodu QR
    qr = segno.make_qr(code)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10)
    img_buffer.seek(0)
    
    # Wstawienie kodu QR do PDF
    pdf.image(img_buffer, x=25, y=25, w=50)
    return pdf.output()

st.title("Generator QR do PDF 🚀")
st.write("Wgraj plik CSV, aby wygenerować paczkę PDF-ów.")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    # Odczytujemy pierwszą linię, żeby wyciągnąć nazwę/wartość 
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    header = content[0].split("_")[-1] # Wyciąga "50PLN" z "NOWY_SKLEP_50PLN"
    
    # Odczytujemy kody (pomijając pierwszą linię nagłówka)
    df = pd.read_csv(uploaded_file, skiprows=1, header=None)
    kody = df[0].astype(str).tolist()
    
    if st.button(f"Generuj {len(kody)} plików PDF"):
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            progress_bar = st.progress(0)
            for i, kod in enumerate(kody):
                pdf_content = generate_pdf(header, kod)
                zf.writestr(f"kod_{kod}.pdf", pdf_content)
                progress_bar.progress((i + 1) / len(kody))
        
        st.success("Gotowe!")
        st.download_button(
            label="Pobierz paczkę ZIP",
            data=zip_buffer.getvalue(),
            file_name="kody_qr.zip",
            mime="application/zip"
        )