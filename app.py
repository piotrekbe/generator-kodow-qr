import streamlit as st
import pandas as pd
import segno
from fpdf import FPDF
import io
import zipfile
import re
import os

# --- KONFIGURACJA PRO ---
st.set_page_config(page_title="QR Generator", page_icon="🛡️", layout="centered")

# 1. Naprawa spacji (Logic Enhancement)
def fix_label_spacing(text):
    return re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', text)

# 2. Generator PDF (Zoptymalizowany pod kątem pamięci)
def generate_pdf(label_text, qr_code_data, has_fonts):
    pdf = FPDF(unit="mm", format=(100, 100))
    pdf.set_auto_page_break(False, margin=0)
    
    if has_fonts:
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        font_main, font_bold = "DejaVu", "DejaVu"
    else:
        font_main, font_bold = "Helvetica", "Helvetica"

    pdf.add_page()
    
    # Nagłówek (Cena)
    pdf.set_font(font_bold, "B" if not has_fonts else "B", 24)
    pdf.set_y(15)
    pdf.cell(0, 12, txt=label_text, ln=True, align='C')
    
    # QR Code
    qr = segno.make_qr(str(qr_code_data))
    img_buffer = io.BytesIO()
    qr.save(img_buffer, kind='png', scale=10, border=2)
    img_buffer.seek(0)
    pdf.image(img_buffer, x=22.5, y=28, w=55)
    
    # Footer
    pdf.set_font(font_main, "", 10)
    pdf.set_y(86) 
    l1 = "Zeskanuj aplikację" if has_fonts else "Zeskanuj aplikacje"
    pdf.cell(0, 5, txt=l1, ln=True, align='C')
    pdf.cell(0, 5, txt="BPme przy realizacji", ln=True, align='C')
    
    return pdf.output()

# --- LOGIKA APLIKACJI ---

st.title("🚀 QR Generator")
st.markdown("---")

# Sprawdzenie zasobów
has_fonts = os.path.exists("DejaVuSans.ttf") and os.path.exists("DejaVuSans-Bold.ttf")
if not has_fonts:
    st.warning("💡 System działa w trybie uproszczonym (brak czcionek PL na serwerze).")

uploaded_file = st.file_uploader("Wgraj plik CSV z kodami", type="csv")

if uploaded_file:
    # Używamy cache, aby nie przetwarzać pliku przy każdym kliknięciu
    @st.cache_data
    def process_csv(file_bytes):
        content = file_bytes.decode("utf-8").splitlines()
        if not content: return None, []
        
        f_line = content[0].strip()
        if f_line.isdigit() or "_" not in f_line:
            lbl, k_raw = "KOD", content
        else:
            lbl = fix_label_spacing(f_line.split("_")[-1])
            k_raw = content[1:]
        
        return lbl, [k.strip() for k in k_raw if k.strip()]

    label, all_kody = process_csv(uploaded_file.getvalue())
    total = len(all_kody)
    
    st.success(f"Wczytano {total} kodów dla: **{label}**")

    # Parametry paczek
    batch_size = 2000
    num_batches = (total + batch_size - 1) // batch_size

    # Persystencja stanu wyboru paczki
    selected_batch = st.selectbox(
        "Wybierz partię do procesowania:", 
        range(num_batches), 
        format_func=lambda x: f"Partia {x+1} (Rekordy {x*batch_size + 1} - {min((x+1)*batch_size, total)})"
    )

    # Wyświetlenie zakresu
    s_idx = selected_batch * batch_size
    e_idx = min((selected_batch + 1) * batch_size, total)
    current_batch = all_kody[s_idx:e_idx]

    c1, c2 = st.columns(2)
    c1.metric("Od numeru", current_batch[0])
    c2.metric("Do numeru", current_batch[-1])

    # Generowanie - proces z zabezpieczeniem stanu
    if st.button(f"🔥 Przygotuj Partię {selected_batch + 1}", use_container_width=True):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        status = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, kod in enumerate(current_batch):
                pdf_data = generate_pdf(label, kod, has_fonts)
                zf.writestr(f"{kod}.pdf", pdf_data)
                
                if i % 50 == 0 or (i + 1) == len(current_batch):
                    p = (i + 1) / len(current_batch)
                    progress_bar.progress(p)
                    status.text(f"Generowanie: {int(p*100)}%")
        
        # Zapisujemy gotowy ZIP w sesji, aby nie zniknął po kliknięciu pobierania
        st.session_state['ready_zip'] = zip_buffer.getvalue()
        st.session_state['last_batch'] = selected_batch + 1

    # Wyświetl przycisk pobierania tylko jeśli paczka jest gotowa w pamięci sesji
    if 'ready_zip' in st.session_state and st.session_state.get('last_batch') == selected_batch + 1:
        st.divider()
        st.download_button(
            label=f"✅ POBIERZ PACZKĘ {st.session_state['last_batch']}",
            data=st.session_state['ready_zip'],
            file_name=f"kody_qr_partia_{st.session_state['last_batch']}.zip",
            mime="application/zip",
            use_container_width=True
        )
