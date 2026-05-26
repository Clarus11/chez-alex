import streamlit as st
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

# --- PARAMÈTRES TARIFS ---
TARIFS_TRANSAT = {
    "Journée (15€)": 15.0,
    "Demi-journée (12€)": 12.0,
    "2 Heures (7€)": 7.0
}
PRIX_BOISSON = 4.5
PRIX_GLACE = 5.0

# --- STYLE CSS AVANCÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }
    div[data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; gap: 2px !important; align-items: center !important; padding: 0 !important; }
    .stButton > button { width: 100% !important; height: 55px !important; padding: 0px !important; font-size: 11px !important; line-height: 1.1 !important; font-weight: bold !important; border-radius: 6px !important; }
    .allee-verticale { background-color: #fef08a; color: #854d0e; font-weight: bold; text-align: center; padding: 15px 2px; border-radius: 4px; font-size: 10px; writing-mode: vertical-lr; transform: rotate(180deg); height: 55px; display: flex; align-items: center; justify-content: center; }
    .total-ca { background-color: #1e3a8a; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- PROTECTION PAR MOT DE PASSE ---
if "autorise" not in st.session_state:
    st.session_state.autorise = False

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Portail Équipe</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Mot de passe :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary", use_container_width=True):
            if mdp == st.secrets["password"]:
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
else:

    # --- INITIALISATION DE LA BASE DE DONNÉES (MÉMOIRE) ---
    # 1. La Plage (7 lignes x 10 groupes)
    if "plage" not in st.session_state:
        st.session_state.plage = {}
        for l in range(1, 8):
            for g in range(1, 11):
                st.session_state.plage[f"L{l}-G{g}"] = {"statut": "Libre", "client": "", "heure": "", "heure_fin": "", "forfait": "Journée (15€)", "nb_transats": 2, "conso_montant": 0.0, "conso_detail": ""}
    
    # 2. Stocks
    if "stocks" not in st.session_state:
        st.session_state.stocks = {"Boissons (Sodas/Eau)": 100, "Glaces": 50}
    
    # 3. Chiffre d'Affaires
    if "ca_total" not in st.session_state:
        st.session_state.ca_total = 0.0
        
    # 4. Pense-bête (To-do list)
    if "notes" not in st.session_state:
        st.session_state.notes = []

    # 5. Réservations
    if "reservations" not in st.session_state:
        st.session_state.reservations = []

    # --- MENU LATÉRAL DE NAVIGATION ---
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>MENU</h2>", unsafe_allow_html=True)
        st.write("---")
        page = st.radio("Navigation :", [
            "🏖️ Plan de la plage", 
            "📅 Réservations", 
            "🚣 Pédalos", 
            "📦 Stocks", 
            "📊 Chiffre d'Affaires", 
            "📝 Pense-bête"
        ])
        st.write("---")
        if st.button("🔒 Verrouiller l'app"):
            st.session_state.autorise = False
            st.rerun()

    # ==========================================
    # PAGE 1 : PLAN DE LA PLAGE
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h3 style='text-align: center; color: #854d0e;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
        
        # Affichage de la grille
        for l in range(1, 8):
            st.caption(f"Ligne {l}")
            cols = st.columns([1, 1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1])
            
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g-1].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

            with cols[5]: st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

        # FENÊTRE POP-UP (MODAL)
        if "groupe_selectionne" in st.session_state and st.session_state.groupe_selectionne is not None:
            @st.dialog("Gestion de l'emplacement")
            def gerer_place(id_sel):
                info = st.session_state.plage[id_sel]
                l_num, g_num = id_sel.replace("L","").split("-G")
                st.markdown(f"**Emplacement {l_num}-{g_num}**")
                
                if info["statut"] == "Libre":
                    nom = st.text_input("Nom du client :")
                    forfait = st.selectbox("Type de location :", list(TARIFS_TRANSAT.keys()))
                    nb_t = st.number_input("Nombre de transats :", min_value=1, value=2)
                    h_a = st.text_input("Heure d'arrivée :", datetime.now().strftime("%H:%M"))
                    h_f = st.text_input("Heure de fin prévue :", "18:00")
                    
                    if st.button("✅ Installer le client", type="primary", use_container_width=True):
                        if nom:
                            st.session_state.plage[id_sel].update({"statut": "Occupé", "client": nom, "heure": h_a, "heure_fin": h_f, "forfait": forfait, "nb_transats": nb_t})
                            st.session_state.groupe_selectionne = None
                            st.rerun()
                else:
                    st.success(f"👤 **{info['client']}** | {info['forfait']} ({info['nb_transats']} transats)")
                    st.caption(f"Arrivé à {info['heure']} - Départ prévu vers {info['heure_fin']}")
                    
                    st.write("---")
                    st.markdown("**🛒 Ardoise (Consommations)**")
                    c1, c2 = st.columns(2)
                    if c1.button(f"+ Boisson ({PRIX_BOISSON}€)"): 
                        st.session_state.plage[id_sel]["conso_montant"] += PRIX_BOISSON
                        st.session_state.stocks["Boissons (Sodas/Eau)"] -= 1
                        st.rerun()
                    if c2.button(f"+ Glace ({PRIX_GLACE}€)"): 
                        st.session_state.plage[id_sel]["conso_montant"] += PRIX_GLACE
                        st.session_state.stocks["Glaces"] -= 1
                        st.rerun()
                    
                    st.write(f"*Total Consos en cours : {info['conso_montant']} €*")
                    
                    # CALCUL TOTAL
                    prix_loc = info["nb_transats"] * TARIFS_TRANSAT[info["forfait"]]
                    total_final = prix_loc + info["conso_montant"]
                    
                    st.markdown(f"<div style='text-align:center; font-size:24px; font-weight:bold; color:#1e3a8a; padding:10px; background:#f0f9ff; border-radius:8px; margin-top:10px;'>TOTAL À ENCAISSER : {total_final} €</div>", unsafe_allow_html=True)
                    
                    st.write("---")
                    if st.button("💵 ENCAISSER ET LIBÉRER", type="primary", use_container_width=True):
                        # Ajouter au CA Global
                        st.session_state.ca_total += total_final
                        # Remettre à zéro
                        st.session_state.plage[id_sel].update({"statut": "Libre", "client": "", "heure": "", "heure_fin": "", "conso_montant": 0.0})
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                
                if st.button("Fermer la fenêtre", use_container_width=True):
                    st.session_state.groupe_selectionne = None
                    st.rerun()

            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # PAGE 2 : RÉSERVATIONS
    # ==========================================
    elif page == "📅 Réservations":
        st.markdown("<h3 style='color: #854d0e;'>📅 Réservations</h3>", unsafe_allow_html=True)
