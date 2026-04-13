import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF 100x100mm
    pdf = FPDF(unit="mm", format=(100, 100))
    
    # Blokujemy automatyczne dodawanie stron - to gwarantuje 1 stronę w pliku
    pdf.set_auto_page_break(False, margin=0)
    
    pdf.add_page()
    
    # 1. GÓRA: Cena (rozmiar 24, pogrubiona)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, txt=label_text, ln=True, align='C')
    
    # 2. ŚRODEK: Kod QR (rozmiar 70, pozycja y=25)
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=15, y=25, w=70)
    
    # 3. DÓŁ: Napis (Zeskanuj aplikacje...) - czcionka 11, pozycja y=91
    pdf.set_font("Helvetica", "", 11)
    pdf.set_y(91) 
    pdf.cell(0, 4, txt="Zeskanuj aplikacje", ln=True, align='C')
    pdf.cell(0, 4, txt="BPme przy realizacji", ln=True, align='C')
    
    return pdf.output()

# --- Oryginalna logika aplikacji ---
st.title("Generator QR PDF")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8").splitlines()
    # Logika wyciągania ceny z nagłówka
    header_raw = content[0].split("_")[-1]
    # Dodanie spacji w cenie (np. 50PLN -> 50 PLN)
    import re
    header = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', header_raw)
    
    df = pd.read_csv(io.StringIO("\n".join(content[1:])), header=None)
    kody = df[0].astype(str).tolist()
    
    if st.button(f"Generuj {len(kody)} plików PDF"):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i, kod in enumerate(kody):
                pdf_content = generate_pdf(header, kod)
                zf.writestr(f"{kod}.pdf", pdf_content)
                # Pasek postępu dokładnie tak jak wcześniej
                progress_bar.progress((i + 1) / len(kody))
        
        st.success("Gotowe!")
        st.download_button(
            label="Pobierz paczkę ZIP",
            data=zip_buffer.getvalue(),
            file_name="kody_qr.zip",
            mime="application/zip"
        )
