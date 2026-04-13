import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

# 1. Funkcja naprawiająca spacje w cenie
def fix_label_spacing(text):
    return re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)

# 2. Funkcja usuwająca polskie znaki dla standardowych czcionek PDF
def clean_pl(text):
    chars = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z',
             'Ą':'A','Ć':'C','Ę':'E','Ł':'L','Ń':'N','Ó':'O','Ś':'S','Ź':'Z','Ż':'Z'}
    for k, v in chars.items(): text = text.replace(k, v)
    return text

# 3. Funkcja generująca pojedynczy PDF
def generate_pdf(label_text, qr_code_data):
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.set_auto_page_break(False, margin=0)
    pdf.add_page()
    
    # GÓRA: Cena
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_y(15)
    pdf.cell(0, 12, txt=clean_pl(label_text), ln=True, align='C')
    
    # ŚRODEK: Kod QR
    qr = segno.make_qr(str(qr_code_data))
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # DÓŁ: Napis
    pdf.set_font("Helvetica", "", 10)
    pdf.set_y(86) 
    pdf.cell(0, 5, txt=clean_pl("Zeskanuj aplikację"), ln=True, align='C')
    pdf.cell(0, 5, txt=clean_pl("BPme przy realizacji"), ln=True, align='C')
    
    return pdf.output()

# --- Interfejs Aplikacji ---
st.title("Generator QR - Tryb Bezpieczny 🛡️")

uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")

if uploaded_file is not None:
    # Odczyt surowych danych
    raw_content = uploaded_file.getvalue().decode("utf-8").splitlines()
    first_line = raw_content[0].strip()
    
    # Rozpoznawanie czy pierwsza linia to nagłówek czy kod (zabezpieczenie przed błędną kwotą)
    if first_line.isdigit() or "_" not in first_line:
        label = "KOD"
        kody_raw = raw_content
    else:
        label_raw = first_line.split("_")[-1]
        label = fix_label_spacing(label_raw)
        kody_raw = raw_content[1:]

    # Oczyszczenie listy kodów (usuwamy puste linie)
    kody = [k.strip() for k in kody_raw if k.strip()]
    total_kody = len(kody)
    
    st.write(f"Wszystkich kodów w pliku: **{total_kody}**")
    
    # Podział na partie po 2000 sztuk
    batch_size = 2000
    num_batches = (total_kody + batch_size - 1) // batch_size

    batch_idx = st.selectbox(
        "Wybierz partię do wygenerowania:", 
        range(num_batches), 
        format_func=lambda x: f"Partia {x+1}: rekordy {x*batch_size + 1} - {min((x+1)*batch_size, total_kody)}"
    )

    # Precyzyjne wycięcie rekordów dla wybranej partii
    start_i = batch_idx * batch_size
    end_i = min((batch_idx + 1) * batch_size, total_kody)
    current_batch = kody[start_i:end_i]

    # Podgląd kontrolny, aby uniknąć "uciekania" kodów na stykach
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Pierwszy kod w paczce:")
        st.code(current_batch[0])
    with col2:
        st.caption("Ostatni kod w paczce:")
        st.code(current_batch[-1])

    if st.button(f"Generuj ZIP dla Partii {batch_idx + 1}"):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, kod in enumerate(current_batch):
                pdf_content = generate_pdf(label, kod)
                zf.writestr(f"{kod}.pdf", pdf_content)
                
                # Aktualizacja paska co 20 plików
                if i % 20 == 0 or i == len(current_batch) - 1:
                    progress_bar.progress((i + 1) / len(current_batch))
                    status_text.text(f"Przetwarzanie pliku {i+1} z {len(current_batch)}...")
        
        st.success(f"Paczka {batch_idx + 1} gotowa!")
        st.download_button(
            label=f"📥 Pobierz Partię {batch_idx + 1} (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"kody_partia_{batch_idx+1}_{label.replace(' ', '_')}.zip",
            mime="application/zip"
        )
