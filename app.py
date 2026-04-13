import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re
import os

# 1. Funkcja naprawiająca spacje w cenie
def fix_label_spacing(text):
    return re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)

# 2. Funkcja generująca pojedynczy PDF
def generate_pdf(label_text, qr_code_data):
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.set_auto_page_break(False, margin=0)
    
    # Sprawdzamy czy pliki czcionek istnieją na serwerze
    has_fonts = os.path.exists("DejaVuSans.ttf") and os.path.exists("DejaVuSans-Bold.ttf")
    
    if has_fonts:
        # Rejestrujemy czcionkę DejaVu (obsługuje polskie znaki)
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        font_main = "DejaVu"
        font_bold = "DejaVu"
    else:
        # Jeśli brak plików, używamy Helvetiki (bezpieczny fallback)
        font_main = "Helvetica"
        font_bold = "Helvetica"

    pdf.add_page()
    
    # GÓRA: Cena
    pdf.set_font(font_bold, "B" if not has_fonts else "", 24)
    if has_fonts: pdf.set_font("DejaVu", "B", 24)
    
    pdf.set_y(15)
    pdf.cell(0, 12, txt=label_text, ln=True, align='C')
    
    # ŚRODEK: Kod QR
    qr = segno.make_qr(str(qr_code_data))
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # DÓŁ: Napis
    pdf.set_font(font_main, "", 10)
    pdf.set_y(86) 
    
    # Jeśli mamy czcionkę, używamy "ę", jeśli nie - "e"
    txt_l1 = "Zeskanuj aplikację" if has_fonts else "Zeskanuj aplikacje"
    txt_l2 = "BPme przy realizacji"
    
    pdf.cell(0, 5, txt=txt_l1, ln=True, align='C')
    pdf.cell(0, 5, txt=txt_l2, ln=True, align='C')
    
    return pdf.output()

# --- Interfejs Aplikacji ---
st.title("Generator QR")

# Informacja dla użytkownika o czcionkach
if not os.path.exists("DejaVuSans.ttf"):
    st.warning("⚠️ Brak plików czcionek na GitHubie (DejaVuSans.ttf). Polskie znaki będą zamienione na zwykłe (e, a).")

uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")

if uploaded_file is not None:
    raw_content = uploaded_file.getvalue().decode("utf-8").splitlines()
    if not raw_content:
        st.error("Plik jest pusty!")
    else:
        first_line = raw_content[0].strip()
        
        if first_line.isdigit() or "_" not in first_line:
            label = "KOD"
            kody_raw = raw_content
        else:
            label_raw = first_line.split("_")[-1]
            label = fix_label_spacing(label_raw)
            kody_raw = raw_content[1:]

        kody = [k.strip() for k in kody_raw if k.strip()]
        total_kody = len(kody)
        
        st.write(f"Wszystkich kodów: **{total_kody}**")
        
        batch_size = 2000
        num_batches = (total_kody + batch_size - 1) // batch_size

        batch_idx = st.selectbox(
            "Wybierz partię:", 
            range(num_batches), 
            format_func=lambda x: f"Partia {x+1}: rekordy {x*batch_size + 1} - {min((x+1)*batch_size, total_kody)}"
        )

        start_i = batch_idx * batch_size
        end_i = min((batch_idx + 1) * batch_size, total_kody)
        current_batch = kody[start_i:end_i]

        col1, col2 = st.columns(2)
        with col1: st.caption("Pierwszy kod:"); st.code(current_batch[0])
        with col2: st.caption("Ostatni kod:"); st.code(current_batch[-1])

        if st.button(f"Generuj ZIP dla Partii {batch_idx + 1}"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(current_batch):
                    pdf_content = generate_pdf(label, kod)
                    zf.writestr(f"{kod}.pdf", pdf_content)
                    # POPRAWKA: Pasek aktualizuje się co 50 plików LUB na samym końcu
                    if i % 50 == 0 or (i + 1) == len(current_batch):
                        progress_bar.progress((i + 1) / len(current_batch))
            
            st.success(f"Paczka {batch_idx + 1} gotowa!")
            st.download_button(
                label=f"📥 Pobierz ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_partia_{batch_idx+1}.zip",
                mime="application/zip"
            )
