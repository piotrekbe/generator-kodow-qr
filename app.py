import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

def fix_label_spacing(text):
    # Ta funkcja szuka miejsca między cyfrą a literą i wstawia spację
    # Np. "50PLN" zamieni na "50 PLN"
    fixed_text = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)
    return fixed_text

def generate_pdf(label_text, qr_code_data):
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.add_page()
    
    # 1. Dodanie poprawionego tekstu na górze
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, txt=label_text, ln=True, align='C')
    
    # 2. QR
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    
    # 3. Wstawienie QR
    pdf.image(img_buffer, x=15, y=25, w=70)
    
    return pdf.output()

# --- Interfejs Aplikacji ---
st.set_page_config(page_title="Generator QR z CSV", page_icon="🖼️")
st.title("Generator Kodów QR z CSV")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    try:
        raw_bytes = uploaded_file.getvalue()
        text_content = raw_bytes.decode("utf-8").splitlines()
        
        # Pobieramy nagłówek
        first_line = text_content[0]
        
        # Wyciągamy surową etykietę (np. 50PLN)
        raw_label = first_line.split("_")[-1] if "_" in first_line else "KOD"
        
        # TUTAJ DZIEJE SIĘ MAGIA: Naprawiamy spację (50PLN -> 50 PLN)
        label = fix_label_spacing(raw_label)
        
        df = pd.read_csv(io.StringIO("\n".join(text_content[1:])), header=None)
        kody = df[0].astype(str).tolist()
        
        st.success(f"Wykryto wartość: **{label}**")

        if st.button(f"Generuj {len(kody)} plików PDF"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)
            status_text = st.empty()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(kody):
                    pdf_bytes = generate_pdf(label, kod)
                    zf.writestr(f"{kod}.pdf", pdf_bytes)
                    
                    if i % 10 == 0 or i == len(kody) - 1:
                        percent = (i + 1) / len(kody)
                        progress_bar.progress(percent)
                        status_text.text(f"Przetwarzanie: {i+1} / {len(kody)}")

            st.download_button(
                label="📥 Pobierz gotową paczkę ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_qr_{label.replace(' ', '_')}.zip",
                mime="application/zip"
            )

    except Exception as e:
        st.error(f"Wystąpił błąd: {e}")
