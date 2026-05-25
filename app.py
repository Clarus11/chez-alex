import streamlit as st
import pandas as pd

st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.title("🏖️ Gestion des Réservations - Chez Alex 2026")
st.write("Bienvenue dans ton outil de gestion de plage en temps réel.")

# 1. Simulation des données actuelles de ton Google Sheet
if 'reservations' not def st.session_state:
    st.session_state.reservations = pd.DataFrame([
        {"Date": "25/05/2026", "Nom client": "Martin", "Téléphone": "0612345678", "Nombre transats": 2, "Heure prévue": "15h00", "Type": "Abonné", "Emplacement": "1-1", "Notes": ""},
        {"Date": "25/05/2026", "Nom client": "Juliette", "Téléphone": "0987456321", "Nombre transats": 3, "Heure prévue": "11h00", "Type": "Standard", "Emplacement": "1-2", "Notes": ""}
    ])

# 2. Affichage du tableau de bord
st.subheader("📋 Liste des réservations du jour")
st.dataframe(st.session_state.reservations, use_container_width=True)

# 3. Formulaire pour ajouter un client
st.sidebar.header("➕ Nouvelle Réservation")
with st.sidebar.form("form_ajout"):
    date = st.date_input("Date")
    nom = st.text_input("Nom du client")
    tel = st.text_input("Téléphone")
    transats = st.number_input("Nombre de transats", min_value=1, max_value=10, value=2)
    heure = st.time_input("Heure prévue")
    type_client = st.selectbox("Type", ["Standard", "Abonné"])
    emplacement = st.text_input("Emplacement (ex: 1-1)")
    notes = st.text_area("Notes (enfant, préférence...)")
    
    soumettre = st.form_submit_form_button("Enregistrer la réservation")

if soumettre:
    nouvelle_ligne = {
        "Date": date.strftime("%d/%m/%Y"),
        "Nom client": nom,
        "Téléphone": tel,
        "Nombre transats": transats,
        "Heure prévue": heure.strftime("%Hh%M"),
        "Type": type_client,
        "Emplacement": emplacement,
        "Notes": notes
    }
    st.session_state.reservations = pd.concat([st.session_state.reservations, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    st.success(f"Réservation enregistrée pour {nom} !")
    st.rerun()
