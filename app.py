import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

def fix_label_spacing(text):
    return re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)

def clean_pl(text):
    chars = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z',
             'Ą':'A','Ć':'C','Ę':'E','Ł':'L','Ń':'N','Ó':'O','Ś':'S','Ź':'Z','Ż':'Z'}
    for k, v in chars.items(): text = text.replace(k, v)
    return text

def generate_pdf(label_text, qr_code_data):
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.set_auto_page_break(False, margin=0)
    pdf.add_page()
    
    # Cena
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_y(15)
    pdf.cell(0, 12, txt=clean_pl(label_text), ln=True, align='C')
    
    # QR
    qr = segno.make_qr(str(qr_code_data))
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # Napis
    pdf.set_font("Helvetica", "", 10)
    pdf.set_y(86) 
    pdf.cell(0, 5, txt=clean_pl("Zeskanuj aplikację"), ln=True, align='C')
    pdf.cell(0, 5, txt=clean_pl("BPme przy realizacji"), ln=True, align='C')
    
    return pdf.output()

st.title("Generator QR - Tryb Masowy 📦")

uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    first_line = content[0]
    
    # Logika nagłówka
    if first_line.strip().isdigit():
        label = "KOD"
        kody_raw = content
    else:
        label_raw = first_line.split("_")[-1]
        label = fix_label_spacing(label_raw)
        kody_raw = content[1:]

    kody = [k.strip() for k in kody_raw if k.strip()]
    total_kody = len(kody)
    
    st.write(f"Wszystkich kodów: **{total_kody}**")
    
    # Podział na partie (np. po 2000 sztuk)
    batch_size = 2000
    num_batches = (total_kody // batch_size) + (1 if total_kody % batch_size != 0 else 0)
    
    batch_idx = st.selectbox("Wybierz partię do wygenerowania (max 2000 plików na raz):", 
                             range(num_batches), 
                             format_func=lambda x: f"Partia {x+1}: od {x*batch_size + 1} do {min((x+1)*batch_size, total_kody)}")

    start_i = batch_idx * batch_size
    end_i = min((batch_idx + 1) * batch_size, total_kody)
    current_batch = kody[start_i:end_i]

    if st.button(f"Generuj pliki od {start_i+1} do {end_i}"):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, kod in enumerate(current_batch):
                pdf_content = generate_pdf(label, kod)
                zf.writestr(f"{kod}.pdf", pdf_content)
                progress_bar.progress((i + 1) / len(current_batch))
        
        st.success(f"Paczka gotowa!")
        st.download_button(
            label="📥 Pobierz ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"kody_partia_{batch_idx+1}.zip",
            mime="application/zip"
        )
