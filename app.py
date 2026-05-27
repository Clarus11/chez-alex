import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp { background-color: #fdfaf3; }
    
    /* Alignement de la grille des transats */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 3px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* Style des boutons transats */
    .stButton > button {
        width: 100% !important;
        height: 55px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    
    /* Allée centrale compacte */
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

    # Liste officielle des produits et prix
    TARIFS_CONSO = {
        "Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50,
        "Oasis Tropical": 2.50, "Tropico": 2.50, "Fanta Orange": 2.50, "Fanta Citron": 2.50,
        "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Jus Orange Pressé": 5.00,
        "Virgin Mojito": 6.00, "Glace Artisanale": 3.80
    }

    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    
    # Structure de stocks
    if "stocks" not in st.session_state: 
        st.session_state.stocks = {
            "Boissons & Cafés": 150, 
            "Oranges (Jus)": 40, 
            "Menthe & Citrons (Mojito)": 30, 
            "Glaces Artisanales": 60
        }
        
    if "notes" not in st.session_state: st.session_state.notes = []
    if "groupe_selectionne" not in st.session_state: st.session_state.groupe_selectionne = None

    # Carnet de réservations (classé par date)
    if "reservations" not in st.session_state: 
        st.session_state.reservations = {}
        
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
            st.caption(f"Ligne {l}")
            cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
            
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info.get("statut", "Libre") == "Libre" else f"🔴\n{info.get('client', 'Occupé')}"
                if cols[g-1].button(label, key=id_c, type="secondary" if info.get("statut", "Libre") == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

            with cols[5]: st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info.get("statut", "Libre") == "Libre" else f"🔴\n{info.get('client', 'Occupé')}"
                if cols[g].button(label, key=id_c, type="secondary" if info.get("statut", "Libre") == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

        if st.session_state.groupe_selectionne:
            @st.dialog("Gestion de l'emplacement")
            def gerer_place(id_sel):
                # Réparation invisible des vieux caches pour éviter l'erreur KeyError
                if "historique_conso" not in st.session_state.plage[id_sel]:
                    st.session_state.plage[id_sel]["historique_conso"] = []
                if "historique_paye_direct" not in st.session_state.plage[id_sel]:
                    st.session_state.plage[id_sel]["historique_paye_direct"] = []
                if "paye_direct" not in st.session_state.plage[id_sel]:
                    st.session_state.plage[id_sel]["paye_direct"] = 0.0
                if "conso_ardoise" not in st.session_state.plage[id_sel]:
                    st.session_state.plage[id_sel]["conso_ardoise"] = 0.0
                
                info = st.session_state.plage[id_sel]
                num_l, num_g = id_sel.replace("L","").split("-G")
                st.markdown(f"#### Emplacement **{num_l}-{num_g}**")
                
                if info["statut"] == "Libre":
                    nom = st.text_input("👤 Nom du client :")
                    nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=2)
                    h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"))
                    
                    if st.button("✅ Installer le client", type="primary"):
                        if nom:
                            st.session_state.plage[id_sel].update({
                                "statut": "Occupé", "client": nom, "nb_transats": nb_t, "heure_arrivee": h_a,
                                "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                                "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                            })
                            st.session_state.groupe_selectionne = None
                            st.rerun()
                        else:
                            st.error("Nom obligatoire.")

                else:
                    st.markdown(f"👤 **{info['client']}** | 🪑 {info['nb_transats']} transats | ⏰ Arrivée : {info['heure_arrivee']}")
                    h_actuelle = datetime.now().strftime("%H:%M")
                    h_dep = st.text_input("⏳ Heure de départ / calcul :", h_actuelle)
                    
                    frais_transats, heures_passees, libelle_tarif = calculer_tarif_heures(info["heure_arrivee"], h_dep, info["nb_transats"])
                    st.markdown(f"⏱️ *Temps : {heures_passees:.2f}h* — **{libelle_tarif}**")
                    
                    st.write("---")
                    st.write("💰 **Règlement des Transats :**")
                    if not info.get("transats_payes", False):
                        st.warning(f"Montant dû : {frais_transats:.2f} €")
                        if st.button("💵 Encaisser les transats DIRECT (Sur le transat)"):
                            st.session_state.ca_jour += frais_transats
                            st.session_state.plage[id_sel]["transats_payes"] = True
                            st.session_state.plage[id_sel]["prix_transats_encaisse"] = frais_transats
                            st.rerun()
                    else:
                        st.success(f"✅ Transats réglés en direct ({info.get('prix_transats_encaisse', 0.0):.2f} €)")

                    st.write("---")
                    st.write("🛒 **Ajouter une Consommation :**")
                    
                    # Sélection du produit
                    produit_choisi = st.selectbox("Choisir l'article :", list(TARIFS_CONSO.keys()))
                    prix_unitaire = TARIFS_CONSO[produit_choisi]
                    st.info(f"Prix unitaire : {prix_unitaire:.2f} €")
                    
                    # Détermination de la catégorie de stock associée
                    if produit_choisi == "Jus Orange Pressé":
                        cat_stock = "Oranges (Jus)"
                    elif produit_choisi == "Virgin Mojito":
                        cat_stock = "Menthe & Citrons (Mojito)"
                    elif produit_choisi == "Glace Artisanale":
                        cat_stock = "Glaces Artisanales"
                    else:
                        cat_stock = "Boissons & Cafés"

                    col_btn_ard, col_btn_dir = st.columns(2)
                    
                    with col_btn_ard:
                        if st.button("➕ Ajouter à l'Ardoise", use_container_width=True):
                            st.session_state.plage[id_sel]["conso_ardoise"] += prix_unitaire
                            st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                            st.session_state.stocks[cat_stock] -= 1
                            st.rerun()
                            
                    with col_btn_dir:
                        if st.button("⚡ Encaisser Direct", use_container_width=True, type="primary"):
                            st.session_state.ca_jour += prix_unitaire
                            st.session_state.plage[id_sel]["paye_direct"] += prix_unitaire
                            st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                            st.session_state.stocks[cat_stock] -= 1
                            st.rerun()

                    # Résumé des consos sur la fiche
                    if info.get("historique_conso") or info.get("historique_paye_direct"):
                        with st.expander("👀 Voir le détail des consos"):
                            if info.get("historique_conso"):
                                st.write("**Sur l'Ardoise :**")
                                for c in info["historique_conso"]: st.text(f" ⏳ {c}")
                            if info.get("historique_paye_direct"):
                                st.write("**Déjà payé en direct :**")
                                for c in info["historique_paye_direct"]: st.text(f" ✅ {c}")

                    st.write("---")
                    transats_dus = 0.0 if info.get("transats_payes", False) else frais_transats
                    total_du_final = transats_dus + info.get("conso_ardoise", 0.0)
                    
                    st.markdown(f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ EN DIRECT : {info.get('paye_direct', 0.0) + info.get('prix_transats_encaisse', 0.0):.2f} €</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='total-display'>RESTE À PAYER AU DÉPART : {total_du_final:.2f} €</div>", unsafe_allow_html=True)
                    
                    col_f1, col_f2 = st.columns(2)
                    if col_f1.button("💵 ENCAISSER RESTE & LIBÉRER", type="primary"):
                        st.session_state.ca_jour += total_du_final
                        st.session_state.plage[id_sel] = {
                            "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2, 
                            "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0, 
                            "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                        }
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                    if col_f2.button("Fermer"):
                        st.session_state.groupe_selectionne = None
                        st.rerun()

            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # MODULE : PÉDALOS (20€/h)
    # ==========================================
    elif page == "🚣 Pédalos":
        st.markdown("<h3 style='text-align: center; color: #854d0e;'>🚣 GESTION DE LA FLOTTE DE PÉDALOS</h3>", unsafe_allow_html=True)
        st.write("Suivi des départs en mer et encaissement instantané.")
        st.write("---")
        
        for p_id, p_info in st.session_state.pedalos.items():
            with st.container(border=True):
                col_p1, col_p2, col_p3 = st.columns([2, 4, 3])
                
                with col_p1:
                    if p_info["statut"] == "Disponible":
                        st.markdown(f"### 🔵 {p_id}")
                        st.success("Disponible")
                    else:
                        st.markdown(f"### 🚣 {p_id}")
                        st.error("En Mer")
                        
                with col_p2:
                    if p_info["statut"] == "Disponible":
                        nom_p = st.text_input("Nom du client :", key=f"nom_{p_id}", placeholder="Ex: Lucas")
                        duree_p = st.radio("Durée demandée :", ["30 min (15€)", "1h (20€)"], key=f"dur_{p_id}", horizontal=True)
                        h_dep_p = st.text_input("Heure de départ :", datetime.now().strftime("%H:%M"), key=f"hdep_{p_id}")
                    else:
                        st.markdown(f"👤 **Client :** {p_info['client']}")
                        st.markdown(f"⏰ **Départ :** {p_info['heure_depart']} | **Forfait :** {p_info['duree_prevue']}")
                        st.markdown(f"💰 **Montant à régler :** {p_info['total_du']:.2f} €")
                        
                with col_p3:
                    st.write("")
                    if p_info["statut"] == "Disponible":
                        if st.button("🚀 Mettre à l'eau", key=f"btn_l_{p_id}", type="primary", use_container_width=True):
                            if nom_p:
                                prix_p = 15.0 if "30 min" in duree_p else 20.0
                                st.session_state.pedalos[p_id].update({
                                    "statut": "En Mer", "client": nom_p, "heure_depart": h_dep_p, "duree_prevue": duree_p, "total_du": prix_p
                                })
                                st.rerun()
                            else:
                                st.error("Entrez un nom")
                    else:
                        if st.button("💵 Retour & Encaisser", key=f"btn_r_{p_id}", type="primary", use_container_width=True):
                            st.session_state.ca_jour += p_info["total_du"]
                            st.session_state.pedalos[p_id].update({
                                "statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0
                            })
                            st.rerun()

    # ==========================================
    # MODULE : NOTES (TO-DO LIST)
    # ==========================================
    elif page == "📝 Notes (To-Do List)":
        st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
        col_note, col_btn = st.columns([4, 1])
        nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Nettoyer la ligne 3")
        if col_btn.button("Ajouter"):
            if nouvelle_note:
                st.session_state.notes.append(nouvelle_note)
                st.rerun()
        st.write("---")
        notes_a_supprimer = []
        for i, note in enumerate(st.session_state.notes):
            if st.checkbox(note, key=f"note_{i}"):
                notes_a_supprimer.append(i)
        if notes_a_supprimer:
            for i in reversed(notes_a_supprimer): st.session_state.notes.pop(i)
            st.rerun()

    # ==========================================
    # MODULE : STOCKS & FRIGOS
    # ==========================================
    elif page == "📦 Stocks & Frigos":
        st.markdown("<h3 style='color: #854d0e;'>📦 État des Stocks</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🥤 Canettes & Cafés", f"{st.session_state.stocks['Boissons & Cafés']} u")
        c2.metric("🍊 Stock Oranges", f"{st.session_state.stocks['Oranges (Jus)']} u")
        c3.metric("🍃 Menthe & Citrons", f"{st.session_state.stocks['Menthe & Citrons (Mojito)']} u")
        c4.metric("🍦 Glaces Artisanales", f"{st.session_state.stocks['Glaces Artisanales']} u")

    # ==========================================
    # MODULE : CHIFFRE D'AFFAIRES
    # ==========================================
    elif page == "📊 Chiffre d'Affaires":
        st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
        st.metric("Total Encaissé Aujourd'hui", f"{st.session_state.ca_jour:.2f} €")

    # ==========================================
    # MODULE : RÉSERVATIONS
    # ==========================================
 # ==========================================
    # MODULE : RÉSERVATIONS
    # ==========================================
   # ==========================================
    # MODULE : RÉSERVATIONS
    # ==========================================
   # ==========================================
    # MODULE : RÉSERVATIONS
    # ==========================================
    elif page == "📅 Réservations":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>📅 GESTION & PRÉPARATION DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
        st.write("---")

        # 1. LE SYSTÈME DE CONSULTATION / PRÉPARATION (En haut)
        st.markdown("### 🔍 1. Choisir le jour à consulter ou à préparer pour le lendemain")
        date_consultation = st.date_input("Sélectionner la date de travail :", datetime.now().date(), key="date_consult")
        date_consult_str = date_consultation.strftime("%d/%m/%Y")

        if date_consult_str not in st.session_state.reservations:
            st.session_state.reservations[date_consult_str] = []

        # --- FENÊTRE MODALE DU PLAN DE LA PLAGE POUR LA DATE SÉLECTIONNÉE ---
        @st.dialog("Plan de placement pour la date sélectionnée", width="large")
        def modal_placement(date_choisie):
            if "resa_spot_sel" not in st.session_state:
                st.session_state.resa_spot_sel = None
                
            # On extrait les places DÉJÀ PRISES spécifiquement pour CE jour-là
            resas_du_jour = st.session_state.reservations.get(date_choisie, [])
            emplacements_pris = {r["emplacement"]: r["client"] for r in resas_du_jour if r.get("est_place") and r.get("emplacement")}
            
            # Étape A : Afficher la carte de ce jour précis
            if st.session_state.resa_spot_sel is None:
                st.markdown(f"### 🗺️ Agencement de la plage pour le **{date_choisie}**")
                st.caption("Cliquez sur une place libre 🟢 pour y attribuer un client réservé ce jour-là.")
                
                for l in range(1, 8):
                    cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
                    for g in range(1, 6):
                        id_c = f"L{l}-G{g}"
                        libre = id_c not in emplacements_pris
                        # Si pris, on affiche 🔴 avec le début du nom du client
                        btn_label = f"🟢\n{l}-{g}" if libre else f"🔴\n{emplacements_pris[id_c][:5]}"
                        if cols[g-1].button(btn_label, key=f"m_pl_{id_c}_{date_choisie}", disabled=not libre, use_container_width=True):
                            st.session_state.resa_spot_sel = id_c
                            st.rerun()
                            
                    with cols[5]: 
                        st.markdown("<div style='text-align:center; font-size:9px; font-weight:bold; color:#a1a1aa; padding-top:12px;'>A<br>L<br>L<br>É<br>E</div>", unsafe_allow_html=True)
                    
                    for g in range(6, 11):
                        id_c = f"L{l}-G{g}"
                        libre = id_c not in emplacements_pris
                        btn_label = f"🟢\n{l}-{g}" if libre else f"🔴\n{emplacements_pris[id_c][:5]}"
                        if cols[g].button(btn_label, key=f"m_pl_{id_c}_{date_choisie}", disabled=not libre, use_container_width=True):
                            st.session_state.resa_spot_sel = id_c
                            st.rerun()
            
            # Étape B : Choisir le client de ce jour à attribuer à la place cliquée
            else:
                id_sel = st.session_state.resa_spot_sel
                st.markdown(f"### 🎯 Assigner la place **{id_sel}** pour le {date_choisie}")
                
                resas_en_attente = [r for r in resas_du_jour if not r.get("est_place", False)]
                
                if not resas_en_attente:
                    st.info("Tous les clients de ce jour sont placés.")
                else:
                    st.write("Sélectionnez le client à installer :")
                    for i, r in enumerate(resas_du_jour):
                        if not r.get("est_place", False):
                            if st.button(f"👤 {r['client']} ({r['transats']} transats) — Préf: {r['preference']}", use_container_width=True, key=f"set_{date_choisie}_{i}"):
                                # On enregistre la place DIRECTEMENT dans la fiche du client pour ce jour-là
                                r["est_place"] = True
                                r["emplacement"] = id_sel
                                st.session_state.resa_spot_sel = None
                                st.rerun()
                                
                st.write("---")
                if st.button("🔙 Retour à la carte", type="secondary"):
                    st.session_state.resa_spot_sel = None
                    st.rerun()
        # ------------------------------------------------------------------

        st.write("---")
        col_form, col_liste = st.columns([1, 2])

        # 2. PARTIE NOUVELLE RÉSERVATION (Saisie de la date incluse ici)
        with col_form:
            st.markdown("#### ➕ Nouvelle Réservation")
            with st.container(border=True):
                nom_resa = st.text_input("Nom du client :", key="form_nom")
                tel_resa = st.text_input("Téléphone :", key="form_tel")
                nb_t_resa = st.number_input("Nombre de transats :", min_value=1, max_value=10, value=2, key="form_nb")
                pref_resa = st.selectbox("Préférence :", [
                    "Peu importe", "1ère Ligne impératif", "Sur un angle", "Proche de l'allée", "Ombre l'après-midi"
                ], key="form_pref")
                
                # TU CHOISIS LA DATE DIRECTEMENT DANS LE FORMULAIRE ICI :
                date_pour_resa = st.date_input("Date de la réservation :", datetime.now().date(), key="form_date")
                date_pour_resa_str = date_pour_resa.strftime("%d/%m/%Y")
                
                if st.button("Enregistrer la réservation", type="primary", use_container_width=True):
                    if nom_resa:
                        if date_pour_resa_str not in st.session_state.reservations:
                            st.session_state.reservations[date_pour_resa_str] = []
                            
                        st.session_state.reservations[date_pour_resa_str].append({
                            "client": nom_resa,
                            "telephone": tel_resa,
                            "transats": nb_t_resa,
                            "preference": pref_resa,
                            "est_place": False,
                            "emplacement": None
                        })
                        st.success(f"Enregistré pour le {date_pour_resa_str} !")
                        st.rerun()
                    else:
                        st.error("Le nom est obligatoire.")

        # 3. LISTE DES PERSONNES QUI ONT RÉSERVÉ POUR LA DATE SÉLECTIONNÉE EN HAUT
        with col_liste:
            st.markdown(f"#### 📋 Liste des réservations du **{date_consult_str}**")
            
            # Bouton pour ouvrir la carte de CE JOUR PRÉCIS
            if st.button(f"🗺️ Placer les clients sur la carte du {date_consult_str}", use_container_width=True):
                st.session_state.resa_spot_sel = None  # Reset
                modal_placement(date_consult_str)
                
            st.write("---")
            
            resas_du_jour = st.session_state.reservations[date_consult_str]
            
            if len(resas_du_jour) == 0:
                st.info(f"Aucune réservation enregistrée pour le {date_consult_str}.")
            else:
                for i, resa in enumerate(resas_du_jour):
                    with st.container(border=True):
                        c_info, c_action = st.columns([5, 1])
                        with c_info:
                            if resa.get("est_place", False):
                                statut_visuel = f"✅ Placé en **{resa.get('emplacement')}**"
                            else:
                                statut_visuel = "⏳ En attente de placement"
                                
                            st.markdown(f"**👤 {resa['client']}** | 🪑 {resa['transats']} transats | *{statut_visuel}*")
                            st.caption(f"📞 {resa['telephone']} | 📍 *{resa['preference']}*")
                        with c_action:
                            if st.button("❌", key=f"del_{date_consult_str}_{i}", help="Supprimer", use_container_width=True):
                                st.session_state.reservations[date_consult_str].pop(i)
                                st.rerun()
