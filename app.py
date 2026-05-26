import streamlit as st
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

# --- STYLE CSS POUR LE RENDU SMARTPHONE (GRILLE DE LA PLAGE) ---
st.markdown("""
    <style>
    /* Mode smartphone : on force les boutons à être carrés et compacts */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        padding: 0px !important;
        font-size: 13px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        margin-bottom: 5px;
    }
    /* Style de l'allée centrale */
    .allee-centrale {
        text-align: center;
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        padding: 6px;
        border-radius: 6px;
        margin: 10px 0;
        font-size: 14px;
        letter-spacing: 2px;
    }
    /* Style du menu latéral */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PROTECTION PAR MOT DE PASSE ---
if "autorise" not in st.session_state:
    st.session_state.autorise = False

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏖️ Chez Alex - Gestion Plage</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Entrez le mot de passe de la plage :", type="password")
        if st.button("Ouvrir l'application 🔓"):
            if mdp == st.secrets["password"]:
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
else:

    # --- INITIALISATION DE LA PLAGE COMPLÈTE (7 LIGNES x 10 GROUPES) ---
    # Si la plage n'existe pas encore en mémoire, on la crée vide
    if "plage" not in st.session_state:
        st.session_state.plage = {}
        for ligne in range(1, 8):
            for groupe in range(1, 11):
                id_case = f"L{ligne}-G{groupe}"
                # Pour le test, on laisse vide. Statut peut être: "Libre" ou "Occupé"
                st.session_state.plage[id_case] = {"statut": "Libre", "client": "", "heure": ""}

    # Variable pour savoir quel groupe est cliqué
    if "groupe_selectionne" not in st.session_state:
        st.session_state.groupe_selectionne = None

    # --- MENU LATÉRAL (TON DESIGN) ---
    with st.sidebar:
        st.markdown("<h3 style='color: #1e3a8a;'>MENU</h3>", unsafe_allow_html=True)
        # Les onglets de ton dessin
        page = st.radio(
            "Navigation :",
            ["🏖️ Plan de la plage", "📅 Réservations", "🚣 Pédalos", "📦 Stocks", "📊 Chiffre d'Affaires", "📝 Notes (Besoins)"]
        )

    # ==========================================
    # ONGLET PRINCIPAL : LE PLAN DE LA PLAGE
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏖️ PLAN DE LA PLAGE</h2>", unsafe_allow_html=True)
        st.write("---")

        # Affichage des 7 lignes
        for ligne in range(1, 8):
            st.markdown(f"**Ligne {ligne}**")
            
            # 5 Groupes à GAUCHE de l'allée
            cols_gauche = st.columns(5)
            for i, col in enumerate(cols_gauche, start=1):
                id_case = f"L{ligne}-G{i}"
                info = st.session_state.plage[id_case]
                
                # Couleur et texte du bouton selon l'état
                if info["statut"] == "Libre":
                    label = f"🟢 Gp {i}\n(Libre)"
                    type_bouton = "secondary"
                else:
                    label = f"🔴 Gp {i}\n{info['client']}\n({info['heure']})"
                    type_bouton = "primary"
                
                if col.button(label, key=id_case, type=type_bouton):
                    st.session_state.groupe_selectionne = id_case

            # L'ALLÉE CENTRALE (Entre le groupe 5 et 6)
            st.markdown("<div class='allee-centrale'>🚧 ALLÉE CENTRALE 🚧</div>", unsafe_allow_html=True)

            # 5 Groupes à DROITE de l'allée
            cols_droite = st.columns(5)
            for i, col in enumerate(cols_droite, start=6):
                id_case = f"L{ligne}-G{i}"
                info = st.session_state.plage[id_case]
                
                if info["statut"] == "Libre":
                    label = f"🟢 Gp {i}\n(Libre)"
                    type_bouton = "secondary"
                else:
                    label = f"🔴 Gp {i}\n{info['client']}\n({info['heure']})"
                    type_bouton = "primary"
                
                if col.button(label, key=id_case, type=type_bouton):
                    st.session_state.groupe_selectionne = id_case
            
            st.write("") # Espace entre les lignes

        # ==========================================
        # FENÊTRE DE DIALOGUE (Quand on clique sur une place)
        # ==========================================
        if st.session_state.groupe_selectionne:
            id_sel = st.session_state.groupe_selectionne
            info_sel = st.session_state.plage[id_sel]
            
            st.write("---")
            st.markdown(f"### ⚙️ Gestion du **{id_sel.replace('-', ' ')}**")
            
            if info_sel["statut"] == "Libre":
                # Formulaire d'installation rapide
                with st.form("installation_client"):
                    nom_c = st.text_input("Nom du client :")
                    heure_a = st.text_input("Heure d'arrivée :", value=datetime.now().strftime("%H:%M"))
                    
                    if st.form_submit_button("✅ Installer"):
                        if nom_c:
                            st.session_state.plage[id_sel] = {"statut": "Occupé", "client": nom_c, "heure": heure_a}
                            st.session_state.groupe_selectionne = None # Ferme la zone de gestion
                            st.rerun()
                        else:
                            st.error("Veuillez entrer un nom.")
            else:
                # Si la place est occupée, on affiche les infos et le bouton de libération
                st.info(f"👤 Client : **{info_sel['client']}** installé à **{info_sel['heure']}**")
                
                # Simulation de l'ardoise (on rajoutera les vrais boutons boissons après)
                st.write("🛒 *Ardoise en cours... (Bientôt les consommations ici)*")
                
                if st.button("💵 Encaisser et Libérer la place", type="primary"):
                    st.session_state.plage[id_sel] = {"statut": "Libre", "client": "", "heure": ""}
                    st.session_state.groupe_selectionne = None
                    st.success("Place libérée !")
                    st.rerun()
                
                if st.button("❌ Fermer sans modifier"):
                    st.session_state.groupe_selectionne = None
                    st.rerun()

    # --- AUTRES PAGES EN ATTENTE ---
    elif page == "📅 Réservations":
        st.info("Page Réservations en cours de préparation...")
    elif page == "🚣 Pédalos":
        st.info("Page Pédalos en cours de préparation...")
    elif page == "📦 Stocks":
        st.info("Page Stocks en cours de préparation...")
    elif page == "📊 Chiffre d'Affaires":
        st.info("Page Chiffre d'Affaires en cours de préparation...")
    elif page == "📝 Notes (Besoins)":
        st.info("Page Notes & Besoins en cours de préparation...")
