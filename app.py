import streamlit as st
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

# --- STYLE CSS AVANCÉ POUR LE RENDU HORIZONTAL ET LA POP-UP ---
st.markdown("""
    <style>
    /* Force les 11 colonnes (5 + allée + 5) à rester sur la même ligne horizontale, même sur téléphone */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 3px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* Style des boutons transats carrés et compacts */
    .stButton > button {
        width: 100% !important;
        height: 55px !important;
        padding: 2px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    
    /* Style mini pour l'allée centrale verticale */
    .allee-verticale {
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        text-align: center;
        padding: 15px 2px;
        border-radius: 4px;
        font-size: 10px;
        writing-mode: vertical-lr; /* Écrit le texte verticalement */
        transform: rotate(180deg);
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
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
    if "plage" not in st.session_state:
        st.session_state.plage = {}
        for ligne in range(1, 8):
            for groupe in range(1, 11):
                id_case = f"L{ligne}-G{groupe}"
                st.session_state.plage[id_case] = {"statut": "Libre", "client": "", "heure": ""}

    # --- MENU LATÉRAL ---
    with st.sidebar:
        st.markdown("<h3 style='color: #1e3a8a;'>MENU</h3>", unsafe_allow_html=True)
        page = st.radio(
            "Navigation :",
            ["🏖️ Plan de la plage", "📅 Réservations", "🚣 Pédalos", "📦 Stocks", "📊 Chiffre d'Affaires", "📝 Notes (Besoins)"]
        )

    # ==========================================
    # ONGLET PRINCIPAL : LE PLAN DE LA PLAGE
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏖️ PLAN DU JOUR</h2>", unsafe_allow_html=True)
        st.write("---")

        # Affichage des 7 lignes de la plage
        for ligne in range(1, 8):
            st.markdown(f"**Ligne {ligne}**")
            
            # On crée 11 colonnes réelles côte à côte : 5 places + 1 allée + 5 places
            colonnes = st.columns([1, 1, 1, 1, 1, 0.6, 1, 1, 1, 1, 1])
            
            # --- Les 5 premiers groupes (Gauche) ---
            for i in range(1, 6):
                id_case = f"L{ligne}-G{i}"
                info = st.session_state.plage[id_case]
                
                if info["statut"] == "Libre":
                    label = f"🟢<br>Gp {i}"
                    type_bouton = "secondary"
                else:
                    label = f"🔴<br>{info['client']}<br>{info['heure']}"
                    type_bouton = "primary"
                
                # On affiche dans la bonne colonne (0 à 4)
                if colonnes[i-1].button(label, key=id_case, type=type_bouton):
                    st.session_state.groupe_selectionne = id_case
                    st.rerun()

            # --- L'allée centrale (Colonne du milieu, index 5) ---
            with colonnes[5]:
                st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

            # --- Les 5 derniers groupes (Droite) ---
            for i in range(6, 11):
                id_case = f"L{ligne}-G{i}"
                info = st.session_state.plage[id_case]
                
                if info["statut"] == "Libre":
                    label = f"🟢<br>Gp {i}"
                    type_bouton = "secondary"
                else:
                    label = f"🔴<br>{info['client']}<br>{info['heure']}"
                    type_bouton = "primary"
                
                # On affiche dans la bonne colonne (index 6 à 10)
                if colonnes[i].button(label, key=id_case, type=type_bouton):
                    st.session_state.groupe_selectionne = id_case
                    st.rerun()
            
            st.write("") # Petit espace sous la ligne

        # ==========================================
        # FENÊTRE POP-UP (MODAL PAR-DESSUS)
        # ==========================================
        # Grâce à st.dialog, la boîte s'ouvre au milieu de l'écran par-dessus le reste !
        @st.dialog("Détails de l'emplacement")
        def ouvrir_fiche_client(id_sel):
            info_sel = st.session_state.plage[id_sel]
            st.markdown(f"### ⚙️ Gestion du **{id_sel.replace('L', 'Ligne ').replace('-G', ' - Groupe ')}**")
            st.write("---")
            
            if info_sel["statut"] == "Libre":
                nom_c = st.text_input("👤 Nom du client :")
                heure_a = st.text_input("⏰ Heure d'arrivée :", value=datetime.now().strftime("%H:%M"))
                
                if st.form_submit_button if False else st.button("✅ Installer le client", type="primary"):
                    if nom_c:
                        st.session_state.plage[id_sel] = {"statut": "Occupé", "client": nom_c, "heure": heure_a}
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                    else:
                        st.error("Veuillez entrer un nom.")
            else:
                st.markdown(f"👤 **Client :** {info_sel['client']}")
                st.markdown(f"⏰ **Arrivé à :** {info_sel['heure']}")
                st.write("---")
                st.write("🛒 **Ardoise / Consommations :**")
                st.caption("(Les boutons boissons arriveront ici à la prochaine étape)")
                
                st.write("---")
                if st.button("💵 Encaisser et libérer", type="primary"):
                    st.session_state.plage[id_sel] = {"statut": "Libre", "client": "", "heure": ""}
                    st.session_state.groupe_selectionne = None
                    st.rerun()
            
            if st.button("❌ Fermer"):
                st.session_state.groupe_selectionne = None
                st.rerun()

        # Si un groupe a été cliqué, on lance la fonction de la pop-up
        if "groupe_selectionne" in st.session_state and st.session_state.groupe_selectionne is not None:
            ouvrir_fiche_client(st.session_state.groupe_selectionne)

    # --- AUTRES PAGES EN ATTENTE ---
    elif page in ["📅 Réservations", "🚣 Pédalos", "📦 Stocks", "📊 Chiffre d'Affaires", "📝 Notes (Besoins)"]:
        st.info(f"Page {page} en cours de préparation...")
