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

def clean_polish_chars(text):
    # Zamiana polskich znaków na odpowiedniki bez ogonków (bezpieczeństwo PDF)
    chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
             'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
    for pol, lat in chars.items():
        text = text.replace(pol, lat)
    return text

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    
    # KLUCZOWE: Wyłączamy automatyczne tworzenie nowej strony
    pdf.set_auto_page_break(auto=False, margin=0)
    
    pdf.add_page()
    
    # 1. GÓRA: Wartość (np. 50 PLN)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_y(10) # Odstęp od samej góry
    pdf.cell(0, 10, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Kod QR
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    
    # Pozycja x=15, y=22, szerokość=70 (klasyczny rozmiar)
    pdf.image(img_buffer, x=15, y=22, w=70)
    
    # 3. DÓŁ: Napis (Zeskanuj aplikacje...)
    # Przesuwamy kursor na dół, ale tak, by nie wybiło nowej strony (y=92)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_y(88) 
    
    line1 = clean_polish_chars("Zeskanuj aplikację")
    line2 = clean_polish_chars("BPme przy realizacji")
    
    pdf.cell(0, 5, txt=line1, ln=True, align='C')
    pdf.cell(0, 5, txt=line2, ln=True, align='C')
    
    return pdf.output()

# --- Interfejs Streamlit ---
st.set_page_config(page_title="Generator QR PDF", page_icon="⛽")
st.title("Generator Kodów QR (1 strona PDF)")

uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")

if uploaded_file is not None:
    try:
        raw_bytes = uploaded_file.getvalue()
        text_content = raw_bytes.decode("utf-8").splitlines()
        
        first_line = text_content[0]
        raw_label = first_line.split("_")[-1] if "_" in first_line else "KOD"
        label = fix_label_spacing(raw_label)
        
        df = pd.read_csv(io.StringIO("\n".join(text_content[1:])), header=None)
        kody = df[0].astype(str).tolist()
        
        st.success(f"Wykryto: {label}. Przygotowano {len(kody)} kodów.")

        if st.button("Generuj PDFy"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(kody):
                    pdf_bytes = generate_pdf(label, kod)
                    zf.writestr(f"{kod}.pdf", pdf_bytes)
                    if i % 10 == 0:
                        progress_bar.progress((i + 1) / len(kody))

            st.download_button(
                label="📥 Pobierz paczkę ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_{label.replace(' ', '_')}.zip",
                mime="application/zip"
            )

    except Exception as e:
        st.error(f"Błąd: {e}")
