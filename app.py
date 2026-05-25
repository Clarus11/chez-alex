import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Pilotage Chez Alex", page_icon="🏖️", layout="wide")

# --- SYSTÈME DE SÉCURITÉ ---
def verifier_mot_de_passe():
    """Retourne True si l'utilisateur a entré le bon mot de passe."""
    if "authentifie" not in st.session_state:
        st.session_state.authentifie = False

    # Si déjà connecté, on ne demande plus rien
    if st.session_state.authentifie:
        return True

    # Affichage de la page de connexion
    st.markdown("<h2 style='text-align: center;'>🔒 Accès Sécurisé - Chez Alex</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp_saisi = st.text_input("Veuillez entrer le mot de passe de la plage :", type="password")
        bouton_connexion = st.button("Se connecter")
        
        if bouton_connexion:
            # On compare avec le mot de passe caché dans les "Secrets" de Streamlit
            if mdp_saisi == st.secrets["password"]:
                st.session_state.authentifie = True
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    return False

# On vérifie la sécurité. Si c'est faux, on arrête le code ici.
if verifier_mot_de_passe():

    # --- LE VRAI CONTENU DU SITE (Invisible tant que le mot de passe n'est pas bon) ---
    st.title("🏖️ Centre de Pilotage - Chez Alex 2026")
    st.write("Bienvenue dans ton espace sécurisé.")

    # Initialisation des données de test basées sur ton Google Sheet
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

    # --- BARRE LATÉRALE : AJOUT RAPIDE ---
    with st.sidebar:
        st.header("➕ Nouveau Client")
        with st.form("ajout_form", clear_on_submit=True):
            f_date = st.date_input("Date")
            f_nom = st.text_input("Nom")
            f_tel = st.text_input("Téléphone")
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

    # --- TABLEAU DE BORD (STATS COIN SUPERIEUR) ---
    col1, col2, col3 = st.columns(3)
    total_transats = st.session_state.reservations["Nombre transats"].sum()
    ca_estime = total_transats * 20 # Exemple à 20€ le transat

    with col1:
        st.metric("Total Transats Loués", f"{total_transats}")
    with col2:
        st.metric("Nombre de réservations", len(st.session_state.reservations))
    with col3:
        st.metric("Recette estimée", f"{ca_estime} €")

    st.divider()

    # --- PLANNING INTERACTIF MODIFIABLE ---
    st.subheader("📝 Planning Interactif")
    st.info("💡 Double-clique dans une case pour modifier une information en direct !")

    edited_df = st.data_editor(
        st.session_state.reservations,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Statut": st.column_config.SelectboxColumn(options=["En attente", "Confirmé", "Arrivé", "Annulé"]),
            "Type": st.column_config.SelectboxColumn(options=["Standard", "Abonné"])
        }
    )

    if st.button("💾 Enregistrer les modifications du tableau"):
        st.session_state.reservations = edited_df
        st.success("Toutes les modifications ont été enregistrées avec succès !")
        st.rerun()

    # --- DECONNEXION ---
    if st.sidebar.button("🚪 Quitter la session"):
        st.session_state.authentifie = False
        st.rerun()
