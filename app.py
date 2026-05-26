import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE (OPTIMISÉ MOBILE)
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp { background-color: #fdfaf3; }
    
    /* Alignement vertical compact pour mobile */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        padding: 0 !important;
    }
    
    /* Style des boutons transats */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        padding: 0px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* Bandeau Allée Centrale */
    .allee-centrale {
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        text-align: center;
        padding: 8px 0px;
        border-radius: 6px;
        font-size: 14px;
        margin: 5px 0px;
        letter-spacing: 1px;
    }
    
    /* Blocs financiers */
    .total-display {
        background-color: #1e3a8a; color: white; padding: 12px; 
        border-radius: 8px; text-align: center; font-size: 18px; 
        font-weight: bold; margin-top: 10px; margin-bottom: 10px;
    }
    .paye-direct-display {
        background-color: #10b981; color: white; padding: 10px; 
        border-radius: 8px; text-align: center; font-size: 14px; 
        font-weight: bold; margin-top: 10px; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CALCUL DYNAMIQUE DES TARIFS PAR HEURES
# ==========================================
def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    try:
        t1 = datetime.strptime(heure_arr, "%H:%M")
        t2 = datetime.strptime(heure_dep, "%H:%M")
        diff = t2 - t1
        minutes = diff.total_seconds() / 60
        if minutes < 0:
            minutes = 0
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
# 3. SÉCURITÉ D'ACCÈS
# ==========================================
if "autorise" not in st.session_state:
    st.session_state.autorise = False

mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Équipe</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Mot de passe :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary"):
            if mdp == mdp_secret:
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
else:
    # ==========================================
    # 4. INITIALISATION DES STRUCTURES DE DONNÉES
    # ==========================================
    if "plage" not in st.session_state:
        st.session_state.plage = {}

    # Initialisation ou réparation complète de chaque emplacement pour éviter les KeyError
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            if id_c not in st.session_state.plage or not isinstance(st.session_state.plage[id_c], dict) or "statut" not in st.session_state.plage[id_c]:
                st.session_state.plage[id_c] = {
                    "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2, 
                    "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, 
                    "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                }
    
    # Flotte de Pédalos
    if "pedalos" not in st.session_state:
        st.session_state.pedalos = {}
        for p in range(1, 6):
            st.session_state.pedalos[f"Pédalo {p}"] = {
                "statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0
            }

    # Tarifs officiels mis à jour
    TARIFS_CONSO = {
        "Coca-Cola": 2.50,
        "Coca-Cola Zero": 2.50,
        "Orangina": 2.50,
        "Schweppes Agrume": 2.50,
        "Oasis Tropical": 2.50,
        "Tropico": 2.50,
        "Fanta Orange": 2.50,
        "Fanta Citron": 2.50,
        "Petite Eau": 1.50,
        "Grande Eau": 2.50,
        "Café / Thé": 1.00,
        "Jus Orange Pressé": 5.00,
        "Virgin Mojito": 6.00,
        "Glace Artisanale": 3.80
    }

    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    
    if "stocks" not in st.session_state: 
        st.session_state.stocks = {
            "Boissons & Cafés": 150, 
            "Oranges (Jus)": 40, 
            "Menthe & Citrons (Mojito)": 30, 
            "Glaces Artisanales": 60
        }
        
    if "notes" not in st.session_state: st.session_state.notes = []
    if "groupe_selectionne" not in st.session_state: st.session_state.groupe_selectionne = None

    # ==========================================
    # 5. NAVIGATION LATÉRALE
    # ==========================================
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>CHEZ ALEX</h2>", unsafe_allow_html=True)
        st.write("---")
        page = st.radio("Navigation :", [
            "🏖️ Plan de la plage", 
            "🚣 Pédalos",
            "📝 Notes (To-Do List)",
            "📦 Stocks & Frigos", 
            "📊 Chiffre d'Affaires",
            "📅 Réservations"
        ])
        st.write("---")
        if st.button("🔒 Verrouiller l'app"):
            st.session_state.autorise = False
            st.rerun()

    # ==========================================
    # MODULE : PLAN DE LA PLAGE
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
        st.write("")

        for l in range(1, 8):
            st.markdown(f"**Ligne {l}**")
            
            # Groupes 1 à 5
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                statut_actuel = info.get("statut", "Libre")
                
                if statut_actuel == "Libre":
                    label = f"🟢 Gp {g} (Libre)"
                    type_btn = "secondary"
                else:
                    label = f"🔴 {info.get('
