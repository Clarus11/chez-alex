         import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 3px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    .stButton > button {
        width: 100% !important;
        height: 55px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    .allee-verticale {
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        text-align: center;
        padding: 10px 1px;
        border-radius: 4px;
        font-size: 9px;
        writing-mode: vertical-lr;
        transform: rotate(180deg);
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .total-display { background-color: #1e3a8a; color: white; padding: 12px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin-top: 10px; margin-bottom: 10px; }
    .paye-direct-display { background-color: #10b981; color: white; padding: 10px; border-radius: 8px; text-align: center; font-size: 14px; font-weight: bold; margin-top: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_html=True)

# ==========================================
# 2. CALCUL TARIFS HEURES
# ==========================================
def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    try:
        t1 = datetime.strptime(heure_arr, "%H:%M")
        t2 = datetime.strptime(heure_dep, "%H:%M")
        diff = t2 - t1
        minutes = diff.total_seconds() / 60
        if minutes < 0: minutes = 0
        heures = minutes / 60
        if heures <= 2.0:
            prix_u = 7.0
            libelle = f"Tarif 2h ({prix_u}€ × {nb_transats})"
        elif heures <= 5.0:
            prix_u = 12.0
            libelle = f"Tarif Demi-journée ({prix_u}€ × {nb_transats})"
        else:
            prix_u = 15.0
            libelle = f"Tarif Journée ({prix_u}€ × {nb_transats})"
        return prix_u * nb_transats, heures, libelle
    except:
        return 15.0 * nb_transats, 0.0, "Tarif Journée (Défaut)"

# ==========================================
# 3. SÉCURITÉ ET INITIALISATION
# ==========================================
if "autorise" not in st.session_state: st.session_state.autorise = False

mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Équipe</h2>", unsafe_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Mot de passe :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary"):
            if mdp == mdp_secret:
                st.session_state.autorise = True
                st.rerun()
            else: st.error("Mot de passe incorrect ❌")
else:
    # --- INITIALISATION GÉNÉRALE ---
    if "plage" not in st.session_state: st.session_state.plage = {}
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            if id_c not in st.session_state.plage:
                st.session_state.plage[id_c] = {"statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2, "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []}
    
    if "pedalos" not in st.session_state:
        st.session_state.pedalos = {f"Pédalo {p}": {"statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0} for p in range(1, 6)}
    
    # LA PARTIE STOCKAGE ESSENTIELLE
    if "stocks" not in st.session_state: 
        st.session_state.stocks = {"Boissons & Cafés": 150, "Oranges (Jus)": 40, "Menthe & Citrons (Mojito)": 30, "Glaces Artisanales": 60}
    
    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    if "notes" not in st.session_state: st.session_state.notes = []
    if "groupe_selectionne" not in st.session_state: st.session_state.groupe_selectionne = None

    TARIFS_CONSO = {"Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50, "Oasis Tropical": 2.50, "Tropico": 2.50, "Fanta Orange": 2.50, "Fanta Citron": 2.50, "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Jus Orange Pressé": 5.00, "Virgin Mojito": 6.00, "Glace Artisanale": 3.80}

    # ==========================================
    # NAVIGATION
    # ==========================================
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>CHEZ ALEX</h2>", unsafe_allow_html=True)
        page = st.radio("Navigation :", ["🏖️ Plan de la plage", "🚣 Pédalos", "📝 Notes (To-Do List)", "📦 Stocks & Frigos", "📊 Chiffre d'Affaires"])
        if st.button("🔒 Verrouiller"): st.session_state.autorise = False; st.rerun()

    # ==========================================
    # PLAN PLAGE & GESTION
    # ==========================================
    if page == "🏖️ Plan de la plage":
        for l in range(1, 8):
            st.caption(f"Ligne {l}")
            cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                if cols[g-1].button(f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}", key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"): st.session_state.groupe_selectionne = id_c; st.rerun()
            with cols[5]: st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)
            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                if cols[g].button(f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}", key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"): st.session_state.groupe_selectionne = id_c; st.rerun()

        if st.session_state.groupe_selectionne:
            @st.dialog("Gestion")
            def gerer_place(id_sel):
                info = st.session_state.plage[id_sel]
                if info["statut"] == "Libre":
                    nom = st.text_input("👤 Nom :")
                    nb_t = st.number_input("🪑 Transats :", 1, 4, 2)
                    h_a = st.text_input("⏰ Arrivée :", datetime.now().strftime("%H:%M"))
                    if st.button("✅ Installer"):
                        if nom: st.session_state.plage[id_sel].update({"statut": "Occupé", "client": nom, "nb_transats": nb_t, "heure_arrivee": h_a}); st.session_state.groupe_selectionne = None; st.rerun()
                else:
                    # GESTION CONSO AVEC STOCKS
                    produit = st.selectbox("Article :", list(TARIFS_CONSO.keys()))
                    prix = TARIFS_CONSO[produit]
                    cat = "Oranges (Jus)" if produit == "Jus Orange Pressé" else "Menthe & Citrons (Mojito)" if produit == "Virgin Mojito" else "Glaces Artisanales" if produit == "Glace Artisanale" else "Boissons & Cafés"
                    
                    c1, c2 = st.columns(2)
                    if c1.button("➕ Ardoise"): 
                        info["conso_ardoise"] += prix; info["historique_conso"].append(produit); st.session_state.stocks[cat] -= 1; st.rerun()
                    if c2.button("⚡ Payé"): 
                        st.session_state.ca_jour += prix; info["paye_direct"] += prix; info["historique_paye_direct"].append(produit); st.session_state.stocks[cat] -= 1; st.rerun()
                    
                    if st.button("💵 Encaisser & Libérer"):
                        st.session_state.ca_jour += info["conso_ardoise"] + (0 if info["transats_payes"] else calculer_tarif_heures(info["heure_arrivee"], datetime.now().strftime("%H:%M"), info["nb_transats"])[0])
                        st.session_state.plage[id_sel] = {"statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2, "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []}; st.session_state.groupe_selectionne = None; st.rerun()
            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # AUTRES PAGES
    # ==========================================
    elif page == "🚣 Pédalos":
        st.write("Gestion des pédalos ici...")
    elif page == "📦 Stocks & Frigos":
        st.subheader("📦 État des Stocks")
        for item, val in st.session_state.stocks.items(): st.metric(item, val)
    elif page == "📊 Chiffre d'Affaires":
        st.metric("Total CA", f"{st.session_state.ca_jour:.2f} €")
