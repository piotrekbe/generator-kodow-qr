# --- POPRAWIONA LOGIKA WYBORU PARTII ---

kody = [k.strip() for k in kody_raw if k.strip()]
total_kody = len(kody)

st.write(f"Wszystkich kodów w pliku: **{total_kody}**")

batch_size = 2000
num_batches = (total_kody + batch_size - 1) // batch_size # Zaokrąglanie w górę

# Wybór partii
batch_idx = st.selectbox(
    "Wybierz partię do wygenerowania:", 
    range(num_batches), 
    format_func=lambda x: f"Partia {x+1}: rekordy {x*batch_size + 1} - {min((x+1)*batch_size, total_kody)}"
)

# Precyzyjne wycięcie rekordów (od start do end)
start_i = batch_idx * batch_size
end_i = min((batch_idx + 1) * batch_size, total_kody)
current_batch = kody[start_i:end_i]

# Wyświetlamy kontrolnie pierwszy i ostatni kod w wybranej partii
st.write(f"Wybrana partia zawiera {len(current_batch)} kodów.")
st.write(f"Pierwszy kod w tej paczce: `{current_batch[0]}`")
st.write(f"Ostatni kod w tej paczce: `{current_batch[-1]}`")

if st.button(f"Generuj pliki z Partii {batch_idx + 1}"):
    # ... (reszta kodu generowania ZIP bez zmian)
