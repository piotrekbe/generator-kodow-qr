import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

def fix_label_spacing(text):
    # Wstawia spację między cyfry a litery (np. 50PLN -> 50 PLN)
    fixed_text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    return fixed_text

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    
    # Blokada automatycznego tworzenia nowej strony
    pdf.set_auto_page_break(False, margin=0)
    pdf.add_page()
    
    # --- OBLICZENIA DLA WYŚRODKOWANIA W PIONIE ---
    # Chcemy, aby cała kompozycja była wyśrodkowana.
    # Ustawiamy sztywne pozycje Y, które sumarycznie dają ładny balans:
    
    # 1. GÓRA: Cena (50 PLN)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_y(15) # Zaczynamy na 15mm od góry
    pdf.cell(0, 12, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Mniejszy kod QR
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    
    # Zmniejszamy szerokość z 70 na 55 mm
    # Pozycja x=22.5 wyśrodkowuje obrazek 55mm na stronie 100mm ( (100-55)/2 )
    # Pozycja y=28 daje odstęp od ceny
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # 3. DÓŁ: Napis z większym odstępem
    pdf.set_font("Helvetica", "", 10)
    
    # Przesunięcie napisu niżej (y=86), aby zwiększyć odstęp od kodu QR
    pdf.set_y(86) 
    
    # Używamy wersji bez polskich znaków dla pełnego bezpieczeństwa przy dużej skali
    pdf.cell(0, 5, txt="Zeskanuj aplikację", ln=True, align='C')
    pdf.cell(0, 5, txt="BPme przy realizacji", ln=True, align='C')
    
    return pdf.output()

# --- Oryginalna logika aplikacji (bez zmian) ---
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
