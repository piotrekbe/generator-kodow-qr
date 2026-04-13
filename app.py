import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

def fix_label_spacing(text):
    # Funkcja wstawia spację między cyfry a litery (np. 50PLN -> 50 PLN)
    fixed_text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    return fixed_text

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.add_page()
    
    # 1. GÓRA: Wartość (np. 50 PLN)
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(0, 15, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Kod QR
    # Generujemy QR
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=1)
    img_buffer.seek(0)
    
    # Wstawiamy obraz (x, y, szerokość) - przesunięty nieco wyżej (y=20)
    pdf.image(img_buffer, x=20, y=18, w=60)
    
    # 3. DÓŁ: Napis informacyjny w dwóch liniach
    # Ustawiamy mniejszą czcionkę dla komunikatu
    pdf.set_font("Helvetica", "", 12)
    
    # Pozycjonujemy kursor pod kodem QR
    pdf.set_y(80) 
    
    # Pierwsza linia
    pdf.cell(0, 6, txt="Zeskanuj aplikację", ln=True, align='C')
    # Druga linia
    pdf.cell(0, 6, txt="BPme przy realizacji", ln=True, align='C')
    
    return pdf.output()

# --- Interfejs Streamlit ---
st.set_page_config(page_title="Generator QR BPme", page_icon="⛽")
st.title("Generator Kodów QR")

uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")

if uploaded_file is not None:
    try:
        raw_bytes = uploaded_file.getvalue()
        text_content = raw_bytes.decode("utf-8").splitlines()
        
        # Pobranie nagłówka i formatowanie ceny
        first_line = text_content[0]
        raw_label = first_line.split("_")[-1] if "_" in first_line else "KOD"
        label = fix_label_spacing(raw_label)
        
        # Odczyt kodów
        df = pd.read_csv(io.StringIO("\n".join(text_content[1:])), header=None)
        kody = df[0].astype(str).tolist()
        
        st.success(f"Wykryta wartość: {label}. Liczba kodów: {len(kody)}")

        if st.button(f"Generuj {len(kody)} plików PDF"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(kody):
                    pdf_bytes = generate_pdf(label, kod)
                    zf.writestr(f"{kod}.pdf", pdf_bytes)
                    
                    if i % 10 == 0 or i == len(kody) - 1:
                        progress_bar.progress((i + 1) / len(kody))

            st.download_button(
                label="📥 Pobierz paczkę ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_{label.replace(' ', '_')}.zip",
                mime="application/zip"
            )

    except Exception as e:
        st.error(f"Błąd: {e}")
