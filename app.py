import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re
import os

def fix_label_spacing(text):
    # Wstawia spację między cyfry a litery (np. 50PLN -> 50 PLN)
    fixed_text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    return fixed_text

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.set_auto_page_break(False, margin=0)
    
    # OBSŁUGA POLSKICH ZNAKÓW:
    # Zakładamy, że pliki czcionek są w tym samym folderze co app.py
    # Jeśli nie chcesz wgrywać czcionek, zostawiamy Helvetica, ale bez ogonków.
    # Poniżej próba wczytania czcionki z obsługą UTF-8:
    try:
        # Musisz wgrać te pliki na GitHub!
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        font_name = 'DejaVu'
    except:
        # Jeśli nie znajdzie plików czcionek, wróci do Helvetiki (bez polskich znaków)
        font_name = 'Helvetica'

    pdf.add_page()
    
    # 1. GÓRA: Cena
    pdf.set_font(font_name, 'B', 24)
    pdf.set_y(15)
    pdf.cell(0, 12, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Kod QR (55mm)
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # 3. DÓŁ: Napis z polskimi znakami
    pdf.set_font(font_name, '', 10)
    pdf.set_y(86) 
    
    # Tekst z polskimi znakami
    line1 = "Zeskanuj aplikację"
    line2 = "BPme przy realizacji"
    
    pdf.cell(0, 5, txt=line1, ln=True, align='C')
    pdf.cell(0, 5, txt=line2, ln=True, align='C')
    
    return pdf.output()

# --- Oryginalna logika aplikacji ---
st.title("Generator QR PDF")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    header_raw = content[0].split("_")[-1]
    header = fix_label_spacing(header_raw)
    
    df = pd.read_csv(io.StringIO("\n".join(content[1:])), header=None)
    kody = df[0].astype(str).tolist()
    
    if st.button(f"Generuj {len(kody)} plików PDF"):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i, kod in enumerate(kody):
                pdf_content = generate_pdf(header, kod)
                zf.writestr(f"{kod}.pdf", pdf_content)
                progress_bar.progress((i + 1) / len(kody))
        
        st.success("Gotowe!")
        st.download_button(
            label="Pobierz paczkę ZIP",
            data=zip_buffer.getvalue(),
            file_name="kody_qr.zip",
            mime="application/zip"
        )
