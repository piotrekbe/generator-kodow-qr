import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re

def generate_pdf(label_text, qr_code_data):
    # Tworzymy PDF o wymiarach 100x100mm (możesz zmienić na A4: "A4")
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.add_page()
    
    # 1. Dodanie tekstu na górze (Wartość np. 50 PLN)
    pdf.set_font("Helvetica", "B", 24)
    # Wyśrodkowanie tekstu
    pdf.cell(0, 20, txt=label_text, ln=True, align='C')
    
    # 2. Generowanie kodu QR za pomocą biblioteki segno
    qr = segno.make_qr(qr_code_data)
    img_buffer = io.BytesIO()
    # Zapisujemy QR do bufora jako PNG
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    
    # 3. Wstawienie kodu QR pod tekstem
    # x=15, y=30 to współrzędne, w=70 to szerokość obrazka w mm
    pdf.image(img_buffer, x=15, y=25, w=70)
    
    return pdf.output()

# --- Interfejs Aplikacji ---
st.set_page_config(page_title="Generator QR PDF", page_icon="🖼️")
st.title("Generator Kodów QR do PDF")
st.info("Wgraj plik CSV, aby otrzymać paczkę plików PDF gotowych do druku.")

uploaded_file = st.file_uploader("Wybierz plik CSV", type="csv")

if uploaded_file is not None:
    try:
        # Odczytujemy surowy tekst, aby wyciągnąć nagłówek z pierwszej linii
        raw_bytes = uploaded_file.getvalue()
        text_content = raw_bytes.decode("utf-8").splitlines()
        
        # Pobieramy pierwszą linię (nagłówek) 
        first_line = text_content[0]
        
        # Logika wyciągania kwoty (szukamy wszystkiego po ostatnim podkreślniku _)
        # Dla "NOWY_SKLEP_50PLN" wyciągnie "50PLN" 
        label = first_line.split("_")[-1] if "_" in first_line else "KOD"
        
        # Wczytujemy kody (pomijając pierwszą linię nagłówka) 
        df = pd.read_csv(io.StringIO("\n".join(text_content[1:])), header=None)
        kody = df[0].astype(str).tolist()
        
        st.success(f"Wykryto nagłówek: **{label}** oraz **{len(kody)}** kodów.")

        if st.button(f"Generuj {len(kody)} plików PDF (ZIP)"):
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)
            status_text = st.empty()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, kod in enumerate(kody):
                    # Generowanie pojedynczego PDF
                    pdf_bytes = generate_pdf(label, kod)
                    # Dodanie do paczki ZIP
                    zf.writestr(f"{kod}.pdf", pdf_bytes)
                    
                    # Aktualizacja paska postępu co 10 kodów (dla szybkości)
                    if i % 10 == 0 or i == len(kody) - 1:
                        percent = (i + 1) / len(kody)
                        progress_bar.progress(percent)
                        status_text.text(f"Przetwarzanie: {i+1} / {len(kody)}")

            status_text.text("✅ Pakowanie zakończone!")
            
            st.download_button(
                label="📥 Pobierz gotową paczkę ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"kody_qr_{label}.zip",
                mime="application/zip"
            )

    except Exception as e:
        st.error(f"Wystąpił błąd podczas odczytu pliku: {e}")
