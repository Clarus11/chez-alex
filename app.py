import streamlit as st
import pandas as pd
import json

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Chez Alex - Gestion Plage", page_icon="🏖️", layout="wide")

# --- STYLE SMARTPHONE & GROS BOUTONS (STYLE RESTO) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 55px;
        font-size: 16px !important;
        font-weight: bold;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .status-card {
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin-bottom: 10px;
    }
    div[data-testid="stHorizontalBlock"] {
        background: #fdfdfd;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ 1 : MOT DE PASSE GENERAL ---
def verifier_mot_de_passe():
    if "authentifie" not in st.session_state:
        st.session_state.authentifie = False
    if st.session_state.authentifie:
        return True

    st.markdown("<h2 style='text-align: center;'>🔒 Accès Sécurisé - Chez Alex</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp_saisi = st.text_input("Mot de passe de la plage :", type="password")
        if st.button("Se connecter 🔓"):
            if mdp_saisi == st.secrets["password"]:
                st.session_state.authentifie = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    return False

if verifier_mot_de_passe():

    # --- INITIALISATION ET SAUVEGARDE LOCALE ---
    # Tarifs fixes
    TARIFS_TRANSATS = {"Journée": 15.0, "Demi-Journée (5h)": 12.0, "2 Heures": 7.0, "Abonné (Suivi)": 0.0}
    TARIFS_CONSO = {
        "Soda": 2.5, "Grande eau": 2.5, "Petite eau": 1.5, 
        "Café / Thé": 1.0, "Jus d'orange": 5.0, "Virgin mojito": 6.0, "Glace": 3.8
    }
    TARIFS_PEDALO = {"30 min": 15.0, "1h": 20.0}

    # Structure de la sauvegarde automatique dans la session
    if 'plage_data' not in st.session_state:
        st.session_state.plage_data = {}
    if 'pedalos' not in st.session_state:
        st.session_state.pedalos = []
    if 'stocks' not in st.session_state:
        st.session_state.stocks = {k: 50 for k in TARIFS_CONSO.keys()} # Par défaut à 50 unités si inconnu

    # Sécurité 2 : Cacher/Afficher les numéros de téléphone à l'écran
    if "voir_tel" not in st.session_state:
        st.session_state.voir_tel = False

    # --- NAVIGATION PRINCIPALE (ONGLETS TACTILES) ---
    onglet = st.radio("Aller à :", ["🏖️ Plan des Transats", "🚣 Pédalos", "📦 Stocks Boissons/Glaces"], horizontal=True)

    st.divider()

    # ==========================================
    # ONGLET 1 : LE PLAN DES TRANSATS (FEUILLE A4)
    # ==========================================
    if onglet == "🏖️ Plan des Transats":
        st.subheader("📋 Plan Interactif de la Plage")
        
        # Bouton d'activation masquage téléphone
        if st.session_state.voir_tel:
            if st.button("👁️ Masquer les numéros de téléphone", type="secondary"):
                st.session_state.voir_tel = False
                st.rerun()
        else:
            if st.button("👁️ Révéler les numéros de téléphone", type="primary"):
                st.session_state.voir_tel = True
                st.rerun()

        # Choix de la ligne de transats (7 lignes au total pour faire 140 transats)
        ligne_choisie = st.selectbox("Sélectionner la Ligne de la plage :", [f"Ligne {i}" for i in range(1, 8)])
        
        st.write("### Cliquez sur un emplacement pour le gérer :")
        
        # Affichage de la ligne (20 transats coupés au milieu par l'allée entre 5 et 6)
        # Partie Gauche (1 à 5)
        col_gauche = st.columns(5)
        for idx, col in enumerate(col_gauche, start=1):
            id_place = f"{ligne_choisie.split()[1]}-{idx}"
            occupe = id_place in st.session_state.plage_data
            label = f"📍 {id_place}\n(Occupé)" if occupe else f"⬜ {id_place}\n(Libre)"
            if col.button(label, key=f"btn_{id_place}"):
                st.session_state.emplacement_actif = id_place

        st.markdown("<div style='text-align:center; color:#ffaa00; font-weight:bold; margin:10px 0;'>🚧 ALLÉE CENTRALE 🚧</div>", unsafe_allow_html=True)
        
        # Partie Droite (6 à 20)
        col_droite = st.columns(15)
        for idx, col in enumerate(col_droite, start=6):
            id_place = f"{ligne_choisie.split()[1]}-{idx}"
            occupe = id_place in st.session_state.plage_data
            label = f"📍 {id_place}" if occupe else f"⬜ {id_place}"
            if col.button(label, key=f"btn_{id_place}"):
                st.session_state.emplacement_actif = id_place

        # ZONE DE RECOMPOSITION (Formulaire Tactile Restaurant)
        if "emplacement_actif" in st.session_state:
            id_p = st.session_state.emplacement_actif
            st.divider()
            st.markdown(f"### ⚙️ Gestion de l'emplacement **{id_p}**")
            
            # Si la place est libre, on propose de l'installer
            if id_p not in st.session_state.plage_data:
                with st.form(f"installation_{id_p}"):
                    nom = st.text_input("Nom du client :")
                    tel = st.text_input("Téléphone :")
                    forfait = st.selectbox("Durée / Forfait :", list(TARIFS_TRANSATS.keys()))
                    notes = st.text_input("Notes (Enfant, etc.) :")
                    
                    if st.form_submit_button("✅ Installer le client"):
                        st.session_state.plage_data[id_p] = {
                            "nom": nom, "tel": tel, "forfait": forfait, "notes": notes,
                            "conso": [], "statut_paiement": "À payer"
                        }
                        st.success(f"Client installé en {id_p}")
                        st.rerun()
            
            # Si la place est occupée, on gère les consos et l'encaissement
            else:
                client = st.session_state.plage_data[id_p]
                
                # Fiche client résumé
                tel_affiche = client['tel'] if st.session_state.voir_tel else "•• •• •• ••"
                st.write(f"**Client :** {client['nom']} | **Tel :** {tel_affiche} | **Forfait :** {client['forfait']}")
                if client['notes']: st.write(f"📝 *Note : {client['notes']}*")
                
                # Calculs financiers en temps réel
                prix_transat = TARIFS_TRANSATS[client['forfait']]
                prix_conso = sum([TARIFS_CONSO[c] for c in client['conso']])
                total_du = prix_transat + prix_conso
                
                # Zone Addition Rapide
                st.markdown(f"#### 💰 Total à régler : **{total_du:.2f} €** *(Transat: {prix_transat}€ | Consos: {prix_conso}€)*")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💵 Encaisser & Libérer les transats", type="primary"):
                        st.session_state.plage_data.pop(id_p)
                        st.success("Emplacement libéré et comptabilisé !")
                        st.rerun()
                with c2:
                    if st.button("❌ Annuler / Libérer sans payer"):
                        st.session_state.plage_data.pop(id_p)
                        st.rerun()

                st.write("---")
                st.write("➕ **Ajouter une consommation sur l'ardoise :**")
                cc1, cc2, cc3 = st.columns(3)
                
                # Boutons de commande tactiles pour le personnel
                for i, item in enumerate(TARIFS_CONSO.keys()):
                    target_col = cc1 if i % 3 == 0 else (cc2 if i % 3 == 1 else cc3)
                    if target_col.button(f"🥤 +1 {item} ({TARIFS_CONSO[item]}€)"):
                        if st.session_state.stocks[item] > 0:
                            st.session_state.plage_data[id_p]['conso'].append(item)
                            st.session_state.stocks[item] -= 1 # Baisse automatique du stock
                            st.success(f"Ajouté : 1 {item}")
                            st.rerun()
                        else:
                            st.error(f"Stock épuisé pour {item} !")

                if client['conso']:
                    st.write("🛒 **Détail actuel des consommations :**")
                    st.text(", ".join(client['conso']))

    # ==========================================
    # ONGLET 2 : LA PAGE SPÉCIALE PÉDALOS
    # ==========================================
    elif onglet == "🚣 Pédalos":
        st.subheader("🚣 Sorties et Locations de Pédalos")
        
        with st.form("ajout_pedalo"):
            p_nom = st.text_input("Nom du loueur :")
            p_duree = st.selectbox("Durée du Pédalo :", ["30 min", "1h"])
            if st.form_submit_button("🚀 Lancer le Pédalo"):
                st.session_state.pedalos.append({
                    "nom": p_nom, "duree": p_duree, "prix": TARIFS_PEDALO[p_duree], "statut": "En mer"
                })
                st.rerun()
                
        st.write("### ⏱️ Locations en cours / Journée")
        if not st.session_state.pedalos:
            st.info("Aucun pédalo en mer pour l'instant.")
        else:
            for idx, pedalo in enumerate(st.session_state.pedalos):
                col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                with col_p1:
                    st.write(f"👤 **{pedalo['nom']}** ({pedalo['duree']}) - Prix : {pedalo['prix']}€")
                with col_p2:
                    st.warning(f"Status: {pedalo['statut']}")
                with col_p3:
                    if pedalo['statut'] == "En mer":
                        if st.button("💰 Encaisser le retour", key=f"ped_{idx}"):
                            st.session_state.pedalos[idx]['statut'] = "Payé & Retourné"
                            st.rerun()

    # ==========================================
    # ONGLET 3 : GESTION DES STOCKS
    # ==========================================
    elif onglet == "📦 Stocks Boissons/Glaces":
        st.subheader("📦 Inventaire & Stocks en temps réel")
        st.write("Le stock descend tout seul à chaque fois que tu ajoutes une boisson sur les transats.")
        
        for item, qte in st.session_state.stocks.items():
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                st.write(f"**{item}**")
                if qte <= 5:
                    st.error(f"⚠️ Alerte ! Plus que {qte} restants !")
                else:
                    st.success(f"Quantité disponible : {qte}")
            with col_s2:
                nouvelle_qte = st.number_input("Ajuster le stock :", min_value=0, value=qte, key=f"stock_{item}")
                if nouvelle_qte != qte:
                    st.session_state.stocks[item] = nouvelle_qte
                    st.rerun()

    # --- BARRE DE DECONNEXION ---
    if st.sidebar.button("🚪 Fermer la session"):
        st.session_state.authentifie = False
        st.rerun()
