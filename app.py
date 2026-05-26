import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE (PROPRE MOBILE)
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp { background-color: #fdfaf3; }
    
    /* Grille des transats responsive et propre */
    .block-container { padding-top: 2rem !important; }
    
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
# 2. SÉCURITÉ D'ACCÈS
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
    # 3. INITIALISATION DES STRUCTURES DE DONNÉES
    # ==========================================
    if "plage" not in st.session_state:
        st.session_state.plage = {}

    # Initialisation complète sans faille
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            if id_c not in st.session_state.plage:
                st.session_state.plage[id_c] = {
                    "statut": "Libre", "client": "", "nb_transats": 2, "forfait": "Journée (15€)",
                    "heure_arrivee": "17:05", "fin_prevue": "18:00",
                    "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, 
                    "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                }
    
    if "pedalos" not in st.session_state:
        st.session_state.pedalos = {}
        for p in range(1, 6):
            st.session_state.pedalos[f"Pédalo {p}"] = {
                "statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0
            }

    TARIFS_CONSO = {
        "Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50,
        "Oasis Tropical": 2.50, "Tropico": 2.50, "Fanta Orange": 2.50, "Fanta Citron": 2.50,
        "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Jus Orange Pressé": 5.00,
        "Virgin Mojito": 6.00, "Glace Artisanale": 3.80
    }

    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    
    if "stocks" not in st.session_state: 
        st.session_state.stocks = {
            "Boissons & Cafés": 150, "Oranges (Jus)": 40, "Menthe & Citrons (Mojito)": 30, "Glaces Artisanales": 60
        }
        
    if "notes" not in st.session_state: st.session_state.notes = []
    if "groupe_selectionne" not in st.session_state: st.session_state.groupe_selectionne = None

    # ==========================================
    # 4. NAVIGATION LATÉRALE
    # ==========================================
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>MENU</h2>", unsafe_allow_html=True)
        page = st.radio("Aller à :", [
            "🏖️ Plan de la plage", "🚣 Pédalos", "📝 Notes (To-Do List)", 
            "📦 Stocks & Frigos", "📊 Chiffre d'Affaires", "📅 Réservations"
        ], label_visibility="collapsed")
        st.write("---")
        if st.button("🔒 Verrouiller"):
            st.session_state.autorise = False
            st.rerun()

    # ==========================================
    # MODULE : PLAN DE LA PLAGE
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>🏖️ PLAN DE LA PLAGE</h3>", unsafe_allow_html=True)
        
        for l in range(1, 8):
            st.write(f"**Ligne {l}**")
            
            # Côté Gauche (Groupes 1 à 5)
            cols_gauche = st.columns(5)
            for idx, g in enumerate(range(1, 6)):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢 Gp {g} (Libre)" if info["statut"] == "Libre" else f"🔴 {info['client']}"
                if cols_gauche[idx].button(label, key=id_c, use_container_width=True):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()
            
            # Allée centrale propre
            st.markdown("<div style='background-color: #fef08a; color: #854d0e; text-align: center; font-weight: bold; padding: 4px; border-radius: 4px; margin: 4px 0;'>🚧 ALLÉE CENTRALE 🚧</div>", unsafe_allow_html=True)
            
            # Côté Droite (Groupes 6 à 10)
            cols_droite = st.columns(5)
            for idx, g in enumerate(range(6, 11)):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢 Gp {g} (Libre)" if info["statut"] == "Libre" else f"🔴 {info['client']}"
                if cols_droite[idx].button(label, key=id_c, use_container_width=True):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()
            st.write("---")

        # Fenêtre de gestion
        if st.session_state.groupe_selectionne:
            @st.dialog("Gestion de l'emplacement")
            def gerer_place(id_sel):
                info = st.session_state.plage[id_sel]
                num_l, num_g = id_sel.replace("L","").split("-G")
                st.markdown(f"### Emplacement {num_l}-{num_g}")
                
                if info["statut"] == "Libre":
                    nom = st.text_input("👤 Nom du client :")
                    nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=10, value=2)
                    
                    forfait = st.radio("💰 Forfait choisi :", [
                        "Journée (15€)", "Demi-journée (12€)", "2 heures (7€)"
                    ])
                    
                    col_h1, col_h2 = st.columns(2)
                    h_a = col_h1.text_input("⏰ Arrivée :", datetime.now().strftime("%H:%M"))
                    h_f = col_h2.text_input("⏳ Fin prévue :", "18:00")
                    
                    if st.button("✅ Installer le client", type="primary", use_container_width=True):
                        if nom:
                            st.session_state.plage[id_sel].update({
                                "statut": "Occupé", "client": nom, "nb_transats": nb_t, "forfait": forfait,
                                "heure_arrivee": h_a, "fin_prevue": h_f
                            })
                            st.session_state.groupe_selectionne = None
                            st.rerun()
                        else:
                            st.error("Le nom du client est obligatoire.")
                else:
                    # Client déjà installé
                    st.markdown(f"👤 **Client :** {info['client']}")
                    st.markdown(f"🪑 **Transats :** {info['nb_transats']} | 📦 **Forfait :** {info['forfait']}")
                    st.markdown(f"⏰ **Arrivée :** {info['heure_arrivee']} | ⏳ **Fin prévue :** {info['fin_prevue']}")
                    
                    # Détermination du tarif unitaire selon le forfait choisi à l'installation
                    if "2 heures" in info["forfait"]:
                        prix_unitaire_t = 7.0
                    elif "Demi-journée" in info["forfait"]:
                        prix_unitaire_t = 12.0
                    else:
                        prix_unitaire_t = 15.0
                        
                    frais_transats = prix_unitaire_t * info["nb_transats"]
                    
                    st.write("---")
                    st.write("💰 **Règlement des Transats :**")
                    if not info["transats_payes"]:
                        st.warning(f"Montant dû pour les transats : {frais_transats:.2f} €")
                        if st.button("💵 Encaisser les transats DIRECT", use_container_width=True):
                            st.session_state.ca_jour += frais_transats
                            st.session_state.plage[id_sel]["transats_payes"] = True
                            st.session_state.plage[id_sel]["prix_transats_encaisse"] = frais_transats
                            st.rerun()
                    else:
                        st.success(f"✅ Transats réglés ({info['prix_transats_encaisse']:.2f} €)")

                    st.write("---")
                    st.write("🛒 **Ajouter une Consommation :**")
                    produit_choisi = st.selectbox("Article :", list(TARIFS_CONSO.keys()))
                    prix_unitaire_c = TARIFS_CONSO[produit_choisi]
                    
                    if produit_choisi == "Jus Orange Pressé": cat_stock = "Oranges (Jus)"
                    elif produit_choisi == "Virgin Mojito": cat_stock = "Menthe & Citrons (Mojito)"
                    elif produit_choisi == "Glace Artisanale": cat_stock = "Glaces Artisanales"
                    else: cat_stock = "Boissons & Cafés"

                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("➕ Ardoise", use_container_width=True):
                        st.session_state.plage[id_sel]["conso_ardoise"] += prix_unitaire_c
                        st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} ({prix_unitaire_c:.2f}€)")
                        st.session_state.stocks[cat_stock] -= 1
                        st.rerun()
                    if c_btn2.button("⚡ Direct", use_container_width=True, type="primary"):
                        st.session_state.ca_jour += prix_unitaire_c
                        st.session_state.plage[id_sel]["paye_direct"] += prix_unitaire_c
                        st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} ({prix_unitaire_c:.2f}€)")
                        st.session_state.stocks[cat_stock] -= 1
                        st.rerun()

                    if info["historique_conso"] or info["historique_paye_direct"]:
                        with st.expander("Détail des consommations"):
                            if info["historique_conso"]:
                                st.write("**Sur l'Ardoise :**")
                                for c in info["historique_conso"]: st.text(f" ⏳ {c}")
                            if info["historique_paye_direct"]:
                                st.write("**Payé en direct :**")
                                for c in info["historique_paye_direct"]: st.text(f" ✅ {c}")

                    st.write("---")
                    transats_dus = 0.0 if info["transats_payes"] else frais_transats
                    total_du_final = transats_dus + info["conso_ardoise"]
                    
                    st.markdown(f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ : {info['paye_direct'] + info['prix_transats_encaisse']:.2f} €</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='total-display'>RESTE À PAYER : {total_du_final:.2f} €</div>", unsafe_allow_html=True)
                    
                    f_btn1, f_btn2 = st.columns(2)
                    if f_btn1.button("💵 TOUT ENCAISSER & LIBÉRER", type="primary", use_container_width=True):
                        st.session_state.ca_jour += total_du_final
                        st.session_state.plage[id_sel] = {
                            "statut": "Libre", "client": "", "nb_transats": 2, "forfait": "Journée (15€)",
                            "heure_arrivee": "17:05", "fin_prevue": "18:00",
                            "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, 
                            "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                        }
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                    if f_btn2.button("Fermer", use_container_width=True):
                        st.session_state.groupe_selectionne = None
                        st.rerun()

            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # MODULE : PÉDALOS
    # ==========================================
    elif page == "🚣 Pédalos":
        st.markdown("<h3 style='text-align: center; color: #854d0e;'>🚣 FLOTTE DE PÉDALOS</h3>", unsafe_allow_html=True)
        for p_id, p_info in st.session_state.pedalos.items():
            with st.container(border=True):
                col_p1, col_p2, col_p3 = st.columns([2, 4, 3])
                with col_p1:
                    st.markdown(f"### {p_id}")
                    if p_info["statut"] == "Disponible": st.success("Disponible")
                    else: st.error("En Mer")
                with col_p2:
                    if p_info["statut"] == "Disponible":
                        nom_p = st.text_input("Client :", key=f"nom_{p_id}")
                        duree_p = st.radio("Durée :", ["30 min (15€)", "1h (20€)"], key=f"dur_{p_id}", horizontal=True)
                        h_dep_p = st.text_input("Départ :", datetime.now().strftime("%H:%M"), key=f"hdep_{p_id}")
                    else:
                        st.markdown(f"👤 **Client :** {p_info['client']}")
                        st.markdown(f"⏰ **Départ :** {p_info['heure_depart']} | **Forfait :** {p_info['duree_prevue']}")
                        st.markdown(f"💰 **À régler :** {p_info['total_du']:.2f} €")
                with col_p3:
                    if p_info["statut"] == "Disponible":
                        if st.button("🚀 Lancer", key=f"btn_l_{p_id}", type="primary", use_container_width=True):
                            if nom_p:
                                prix_p = 15.0 if "30 min" in duree_p else 20.0
                                st.session_state.pedalos[p_id].update({"statut": "En Mer", "client": nom_p, "heure_depart": h_dep_p, "duree_prevue": duree_p, "total_du": prix_p})
                                st.rerun()
                    else:
                        if st.button("💵 Retour", key=f"btn_r_{p_id}", type="primary", use_container_width=True):
                            st.session_state.ca_jour += p_info["total_du"]
                            st.session_state.pedalos[p_id].update({"statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0})
                            st.rerun()

    # ==========================================
    # MODULES COMPLÉMENTAIRES (STOCKS, CA, ETC.)
    # ==========================================
    elif page == "📝 Notes (To-Do List)":
        st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison</h3>", unsafe_allow_html=True)
        col_note, col_btn = st.columns([4, 1])
        nouvelle_note = col_note.text_input("Tâche :")
        if col_btn.button("Ajouter") and nouvelle_note:
            st.session_state.notes.append(nouvelle_note)
            st.rerun()
        st.write("---")
        for i, note in enumerate(st.session_state.notes):
            if st.checkbox(note, key=f"note_{i}"):
                st.session_state.notes.pop(i)
                st.rerun()

    elif page == "📦 Stocks & Frigos":
        st.markdown("<h3 style='color: #854d0e;'>📦 État des Stocks</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🥤 Canettes & Cafés", f"{st.session_state.stocks.get('Boissons & Cafés', 0)} u")
        c2.metric("🍊 Stock Oranges", f"{st.session_state.stocks.get('Oranges (Jus)', 0)} u")
        c3.metric("🍃 Menthe & Citrons", f"{st.session_state.stocks.get('Menthe & Citrons (Mojito)', 0)} u")
        c4.metric("🍦 Glaces Artisanales", f"{st.session_state.stocks.get('Glaces Artisanales', 0)} u")

    elif page == "📊 Chiffre d'Affaires":
        st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
        st.metric("Total Encaissé", f"{st.session_state.ca_jour:.2f} €")

    elif page == "📅 Réservations":
        st.markdown("<h3 style='color: #854d0e;'>📅 Réservations</h3>", unsafe_allow_html=True)
        st.warning("Prêt pour l'étape suivante !")
