import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Pilotage Chez Alex", page_icon="🏖️", layout="wide")

# --- SYSTÈME DE SÉCURITÉ 1 : LE MOT DE PASSE ---
def verifier_mot_de_passe():
    if "authentifie" not in st.session_state:
        st.session_state.authentifie = False

    if st.session_state.authentifie:
        return True

    st.markdown("<h2 style='text-align: center;'>🔒 Accès Sécurisé - Chez Alex</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp_saisi = st.text_input("Veuillez entrer le mot de passe de la plage :", type="password")
        bouton_connexion = st.button("Se connecter")
        
        if bouton_connexion:
            if mdp_saisi == st.secrets["password"]:
                st.session_state.authentifie = True
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    return False

# Fonction pour masquer les numéros de téléphone (Sécurité 2)
def masquer_telephone(tel):
    if pd.isna(tel) or len(str(tel)) < 4:
        return "•• •• •• •• ••"
    tel_str = str(tel)
    return f"{tel_str[:2]} •• •• •• {tel_str[-2:]}"

# Si le premier verrou est passé, on charge le site
if verifier_mot_de_passe():

    # --- INITIALISATION DES DONNÉES ---
    if 'reservations' not in st.session_state:
        st.session_state.reservations = pd.DataFrame([
            {
                "Date": "2026-05-25", "Nom client": "Martin", "Téléphone": "0612345678", 
                "Nombre transats": 2, "Heure prévue": "15:00", "Type": "Abonné", 
                "Statut": "Confirmé", "Emplacement": "1-1", "Notes": "Besoin d'ombre"
            },
            {
                "Date": "2026-05-25", "Nom client": "Juliette", "Téléphone": "0678912345", 
                "Nombre transats": 4, "Heure prévue": "10:30", "Type": "Standard", 
                "Statut": "En attente", "Emplacement": "2-3", "Notes": "Proche bord de l'eau"
            }
        ])

    # Initialisation de l'état du deuxième verrou (Masquage)
    if "reveler_donnees" not in st.session_state:
        st.session_state.reveler_donnees = False

    # --- LE CONTENU DU SITE ---
    st.title("🏖️ Centre de Pilotage - Chez Alex 2026")
    
    # --- BARRE LATÉRALE : AJOUT RAPIDE & DÉCONNEXION ---
    with st.sidebar:
        st.header("➕ Nouveau Client")
        with st.form("ajout_form", clear_on_submit=True):
            f_date = st.date_input("Date")
            f_nom = st.text_input("Nom")
            f_tel = st.text_input("Téléphone (Ex: 0612345678)")
            f_nb = st.number_input("Transats", min_value=1, value=2)
            f_heure = st.time_input("Heure")
            f_type = st.selectbox("Type", ["Standard", "Abonné"])
            f_statut = st.selectbox("Statut", ["En attente", "Confirmé", "Arrivé"])
            f_place = st.text_input("Emplacement")
            f_notes = st.text_area("Notes")
            
            submit = st.form_submit_button("Ajouter à la liste")
            
            if submit:
                nouveau = {
                    "Date": str(f_date), "Nom client": f_nom, "Téléphone": f_tel,
                    "Nombre transats": f_nb, "Heure prévue": str(f_heure)[:5],
                    "Type": f_type, "Statut": f_statut, "Emplacement": f_place, "Notes": f_notes
                }
                st.session_state.reservations = pd.concat([st.session_state.reservations, pd.DataFrame([nouveau])], ignore_index=True)
                st.rerun()
        
        st.write("---")
        if st.button("🚪 Quitter la session", use_container_width=True):
            st.session_state.authentifie = False
            st.rerun()

    # --- STATISTIQUES ---
    col1, col2, col3 = st.columns(3)
    total_transats = st.session_state.reservations["Nombre transats"].sum()
    with col1:
        st.metric("Total Transats Loués", f"{total_transats}")
    with col2:
        st.metric("Nombre de réservations", len(st.session_state.reservations))
    with col3:
        st.metric("Recette estimée (20€/u)", f"{total_transats * 20} €")

    st.divider()

    # --- PLANNING INTERACTIF & SÉCURITÉ 2 ---
    st.subheader("📝 Planning Interactif")
    
    # Bouton d'action pour activer/désactiver le deuxième verrou
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn2:
        if st.session_state.reveler_donnees:
            if st.button("👁️ Masquer les téléphones", type="secondary", use_container_width=True):
                st.session_state.reveler_donnees = False
                st.rerun()
        else:
            if st.button("👁️ Révéler les téléphones", type="primary", use_container_width=True):
                st.session_state.reveler_donnees = True
                st.rerun()

    # Préparation du tableau avec ou sans masquage
    df_affichage = st.session_state.reservations.copy()
    if not st.session_state.reveler_donnees:
        df_affichage["Téléphone"] = df_affichage["Téléphone"].apply(masquer_telephone)

    st.info("💡 Les modifications directes sont bloquées lorsque les téléphones sont masqués pour éviter les erreurs.")

    # Affichage du tableau de bord (modifiable uniquement si révélé, pour la sécurité des données)
    edited_df = st.data_editor(
        df_affichage,
        use_container_width=True,
        num_rows="dynamic",
        disabled=not st.session_state.reveler_donnees, # Bloque l'édition si masqué
        column_config={
            "Statut": st.column_config.SelectboxColumn(options=["En attente", "Confirmé", "Arrivé", "Annulé"]),
            "Type": st.column_config.SelectboxColumn(options=["Standard", "Abonné"])
        }
    )

    # Sauvegarde des modifications
    if st.session_state.reveler_donnees:
        if st.button("💾 Enregistrer les modifications du tableau"):
            st.session_state.reservations = edited_df
            st.success("Toutes les modifications ont été enregistrées avec succès !")
            st.rerun()
