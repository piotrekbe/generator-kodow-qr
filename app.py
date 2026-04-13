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
    # Powrót do Twoich pierwotnych ustawień PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.add_page()
    
    # 1. GÓRA: Wartość (50 PLN) - czcionka BOLD 24 (jak w Twojej pierwszej działającej wersji)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Kod QR (rozmiar w=70, jak w oryginale)
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    
    # Wstawienie kodu QR dokładnie tak, jak miałeś na początku
    pdf.image(img_buffer, x=15, y=25, w=70)
    
    # 3. DÓŁ: Dodatkowy napis (bez polskich znaków, aby uniknąć błędu "ę")
    pdf.set_font("Helvetica", "", 11)
    # Ustawiamy kursor nisko, by nie nachodził na QR
    pdf.set_y(90) 
    pdf.cell(0, 5, txt="Zeskanuj aplikacje", ln=True, align='C')
    pdf.cell(0, 5, txt="BPme przy realizacji", ln=True, align='C')
    
    return pdf.output()

# --- Interfejs Aplikacji (bez zmian) ---
st.set_page_config(page_title="Generator QR PDF", page_icon="⛽")
st.title("Generator Kodów QR do PDF")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    try:
        raw_bytes = uploaded_file.getvalue()
        text_content = raw_bytes.decode("utf-8").splitlines()
        
        first_line = text_content[0]
        raw_label = first_line.split("_")[-1] if "_" in first_line else "KOD"
        label = fix_label_spacing(raw_label)
        
        df = pd.read_csv(io.StringIO("\n".join(text_content[1:])), header=None)
        kody = df[0].astype(str).tolist()
        
        st.success(f"Wykryto wartosc: **{label}**")

        if st.button(f"Generuj {len(kody)} plikow PDF"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(kody):
                    pdf_bytes = generate_pdf(label, kod)
                    zf.writestr(f"{kod}.pdf", pdf_bytes)
                    
                    if i % 10 == 0 or i == len(kody) - 1:
                        progress_bar.progress((i + 1) / len(kody))

            st.download_button(
                label="📥 Pobierz gotowa paczke ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_qr_{label.replace(' ', '_')}.zip",
                mime="application/zip"
            )

    except Exception as e:
        st.error(f"Wystapil blad: {e}")
