import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }
    /* ... ton CSS ici ... */
    </style>
    """, unsafe_allow_html=True)

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
# # 2. CONNEXION GOOGLE SHEETS
# ==========================================
# 1. Définition de l'ID correct (avec le 'l' et non le '1')
ID_SHEET = "1hp2tK4WcDJcWv9ww1ZIuod-nwz8ywaGiNBiSPlYylzE"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. Lecture en utilisant l'ID
    data_plage = conn.read(spreadsheet=ID_SHEET, worksheet="plage", ttl=0)
    
    # 3. Affichage réussi en dehors du bloc d'erreur
    st.sidebar.success("✅ Connecté !")
    st.dataframe(data_plage)

except Exception as e:
    # Ce bloc ne s'affiche que s'il y a un réel problème technique
    st.sidebar.error(f"Erreur de connexion : {e}")
# ==========================================
# 3. CALCUL DYNAMIQUE DES TARIFS PAR HEURES
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
# 4. SÉCURITÉ D'ACCÈS
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
    # 5. INITIALISATION DES STRUCTURES DE DONNÉES
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
    # 6. NAVIGATION LATÉRALE
    # ==========================================
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>CHEZ ALEX</h2>", unsafe_allow_html=True)
        st.write("---")
        page = st.radio("Navigation :", [
            "🏖️ Plan de la plage",
            "📅 Réservations",
            "🛶 Pédalos",
            "📝 Notes (To-Do List)",
            "📦 Stocks & Frigos",
            "📊 Chiffre d'Affaires",
            "📊 Récap Journalier",
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

        # =====================================================================
        # 🟢 AMÉLIORATION : CHARGEMENT AUTOMATIQUE DES RÉSERVATIONS DU JOUR
        # =====================================================================
        # 1. On récupère la date du jour
        date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
        resas_du_jour = st.session_state.reservations.get(date_aujourdhui, [])
        
        # 2. On injecte les réservations si la place est libre sur la plage
        for resa in resas_du_jour:
            place = resa.get("emplacement")
            
            # Sécurité : On vérifie que la place existe dans ton plan et qu'elle est bien "Libre"
            if place and place in st.session_state.plage and st.session_state.plage[place].get("statut", "Libre") == "Libre":
                st.session_state.plage[place].update({
                    "statut": "Occupé", 
                    "client": resa["client"], 
                    "nb_transats": resa.get("transats", 2), 
                    "heure_arrivee": "09:00",  # Heure par défaut le matin (tu pourras la changer en cliquant sur le transat)
                    "transats_payes": False, 
                    "prix_transats_encaisse": 0.0, 
                    "conso_ardoise": 0.0,
                    "historique_conso": [], 
                    "paye_direct": 0.0, 
                    "historique_paye_direct": []
                })
        # =====================================================================

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

                    # 🔴 LA LIGNE DE SOUSTRACTION AUTOMATIQUE QUI ÉTAIT ICI A ÉTÉ SUPPRIMÉE 🔴

                    col_btn_ard, col_btn_dir = st.columns(2)

                    with col_btn_ard:
                        # Ajout d'une key unique pour stabiliser le bouton
                        if st.button("➕ Ajouter à l'Ardoise", key=f"btn_ard_{id_sel}", use_container_width=True):
                            st.session_state.plage[id_sel]["conso_ardoise"] += prix_unitaire
                            st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                            st.session_state.stocks[produit_choisi] -= 1  # 🟢 La déduction se fait UNIQUEMENT ici
                            st.rerun()

                    with col_btn_dir:
                        # Ajout d'une key unique pour stabiliser le bouton      
                        if st.button("⚡ Encaisser Direct", key=f"btn_dir_{id_sel}", use_container_width=True, type="primary"):
                            st.session_state.ca_jour += prix_unitaire
                            st.session_state.plage[id_sel]["paye_direct"] += prix_unitaire
                            st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                            st.session_state.stocks[produit_choisi] -= 1  # 🟢 Et UNIQUEMENT ici
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
    # MODULE : GESTION DES STOCKS
    # ==========================================
    elif page == "📦 Stocks & Frigos":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>📦 GESTION DES STOCKS & FRIGOS</h3>", unsafe_allow_html=True)
        st.write("---")

        st.info("💡 Cet onglet sert uniquement à enregistrer les livraisons (Réassort). Les stocks diminuent automatiquement à chaque vente sur le plan de la plage.")

        # On crée une jolie entête de tableau
        col_h1, col_h2, col_h3 = st.columns([3, 1.5, 2])
        with col_h1: st.markdown("**Produit**")
        with col_h2: st.markdown("**Quantité en réserve**")
        with col_h3: st.markdown("**Ajouter du stock (Réassort)**")
        st.write("---")

        # On boucle sur TOUS les produits présents dans tes tarifs
        for produit in TARIFS_CONSO.keys():
            # Sécurité : si le produit n'existe pas encore dans le stock, on l'initialise à 0
            if produit not in st.session_state.stocks:
                st.session_state.stocks[produit] = 0

            quantite_actuelle = st.session_state.stocks[produit]
        
            # Création de la ligne pour le produit
            col_nom, col_qte, col_actions = st.columns([3, 1.5, 2])
        
            with col_nom:
                st.write(f"🍹 {produit}")
            
            with col_qte:
                # Alerte visuelle : si le stock est à 5 ou moins, on l'affiche en ROUGE
                if quantite_actuelle <= 5:
                    st.markdown(f"<b style='color: #dc2626;'>{quantite_actuelle} ⚠️ (Bas)</b>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<b style='color: #16a34a;'>{quantite_actuelle}</b>", unsafe_allow_html=True)
                
            with col_actions:
                # Uniquement des boutons pour AUGMENTER le stock
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("➕ 1", key=f"plus1_{produit}", use_container_width=True):
                    st.session_state.stocks[produit] += 1
                    st.rerun()
                if btn_col2.button("➕ 10", key=f"plus10_{produit}", use_container_width=True):
                    st.session_state.stocks[produit] += 10
                    st.rerun()
                
        st.write("---")
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
    # MODULE : RÉSERVATIONS (MODE DÉPLACEMENT DIRECT)
    # ==========================================
    elif page == "📅 Réservations":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>📅 GESTION & PRÉPARATION DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
        st.write("---")

        # Initialisation des variables d'état pour le pop-up
        if "show_modal_placement" not in st.session_state:
            st.session_state.show_modal_placement = False
        if "resa_spot_sel" not in st.session_state:
            st.session_state.resa_spot_sel = None
        if "moving_client_idx" not in st.session_state:
            st.session_state.moving_client_idx = None

        # 1. LE SYSTÈME DE CONSULTATION / PRÉPARATION
        st.markdown("### 🔍 1. Choisir le jour à consulter ou à préparer")
        date_consultation = st.date_input("Sélectionner la date de travail :", datetime.now().date(), key="date_consult")
        date_consult_str = date_consultation.strftime("%d/%m/%Y")

        if date_consult_str not in st.session_state.reservations:
            st.session_state.reservations[date_consult_str] = []

        # --- FENÊTRE MODALE AVEC DEPLACEMENT INTUITIF ---
        @st.dialog("Plan de placement - Préparation du lendemain", width="large")
        def modal_placement(date_choisie):
            resas_du_jour = st.session_state.reservations.get(date_choisie, [])
            
            # Dictionnaire pour savoir rapidement qui est sur quelle place { "L1-G1": {"client": "Nom", "index": 0} }
            emplacements_pris = {}
            for idx, r in enumerate(resas_du_jour):
                if r.get("est_place") and r.get("emplacement"):
                    emplacements_pris[r["emplacement"]] = {"nom": r["client"], "index": idx}
            
            col_carte_gauche, col_liste_droite = st.columns([5, 3])
            
            # --- COLONNE GAUCHE : LA CARTE ---
            with col_carte_gauche:
                st.markdown(f"#### 🗺️ Plan du **{date_choisie}**")
                st.caption("🟢 Libre | 🔴 Occupé | 🟡 Sélectionné | 🔵 En cours de déplacement")
                
                for l in range(1, 8):
                    cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
                    
                    # Groupes 1 à 5
                    for g in range(1, 6):
                        id_c = f"L{l}-G{g}"
                        libre = id_c not in emplacements_pris
                        
                        # Vérification du statut visuel de la case
                        is_selectionne = st.session_state.resa_spot_sel == id_c
                        is_en_deplacement = False
                        if st.session_state.moving_client_idx is not None:
                            idx_m = st.session_state.moving_client_idx
                            if resas_du_jour[idx_m].get("emplacement") == id_c:
                                is_en_deplacement = True
                        
                        if is_en_deplacement:
                            btn_label = f"🔵\n{l}-{g}"
                            help_txt = "Client sélectionné pour changement de place"
                        elif is_selectionne:
                            btn_label = f"🟡\n{l}-{g}"
                            help_txt = f"Sélectionné : {id_c}"
                        else:
                            btn_label = f"🟢\n{l}-{g}" if libre else f"🔴\n{l}-{g}"
                            help_txt = "Libre" if libre else f"Occupé par {emplacements_pris[id_c]['nom']}"
                            
                        if cols[g-1].button(btn_label, key=f"m_pl_{id_c}_{date_choisie}", help=help_txt, use_container_width=True):
                            # LOGIQUE AU CLIC SUR LA CARTE
                            if st.session_state.moving_client_idx is not None:
                                if is_en_deplacement:
                                    st.session_state.moving_client_idx = None # Clic sur lui-même = Annuler
                                elif libre:
                                    resas_du_jour[st.session_state.moving_client_idx]["emplacement"] = id_c
                                    st.session_state.moving_client_idx = None
                                else:
                                    st.error("Cette place est déjà prise !")
                                st.rerun()
                            else:
                                st.session_state.resa_spot_sel = id_c
                                st.rerun()
                            
                    # Allée centrale
                    with cols[5]: 
                        st.markdown("<div style='text-align:center; font-size:8px; font-weight:bold; color:#a1a1aa; padding-top:10px;'>|</div>", unsafe_allow_html=True)
                    
                    # Groupes 6 à 10
                    for g in range(6, 11):
                        id_c = f"L{l}-G{g}"
                        libre = id_c not in emplacements_pris
                        
                        is_selectionne = st.session_state.resa_spot_sel == id_c
                        is_en_deplacement = False
                        if st.session_state.moving_client_idx is not None:
                            idx_m = st.session_state.moving_client_idx
                            if resas_du_jour[idx_m].get("emplacement") == id_c:
                                is_en_deplacement = True
                        
                        if is_en_deplacement:
                            btn_label = f"🔵\n{l}-{g}"
                            help_txt = "Client sélectionné pour changement de place"
                        elif is_selectionne:
                            btn_label = f"🟡\n{l}-{g}"
                            help_txt = f"Sélectionné : {id_c}"
                        else:
                            btn_label = f"🟢\n{l}-{g}" if libre else f"🔴\n{l}-{g}"
                            help_txt = "Libre" if libre else f"Occupé par {emplacements_pris[id_c]['nom']}"
                            
                        if cols[g].button(btn_label, key=f"m_pl_{id_c}_{date_choisie}", help=help_txt, use_container_width=True):
                            # LOGIQUE AU CLIC SUR LA CARTE
                            if st.session_state.moving_client_idx is not None:
                                if is_en_deplacement:
                                    st.session_state.moving_client_idx = None
                                elif libre:
                                    resas_du_jour[st.session_state.moving_client_idx]["emplacement"] = id_c
                                    st.session_state.moving_client_idx = None
                                else:
                                    st.error("Cette place est déjà prise !")
                                st.rerun()
                            else:
                                st.session_state.resa_spot_sel = id_c
                                st.rerun()

            # --- COLONNE DROITE : ATTRIBUTION ET ACTIONS RAPIDES ---
            with col_liste_droite:
                st.markdown("#### ⚙️ Action / Attribution")
                
                # CAS A : UN CLIENT EST EN COURS DE DÉPLACEMENT
                if st.session_state.moving_client_idx is not None:
                    client_concerne = resas_du_jour[st.session_state.moving_client_idx]
                    st.warning(f"🔄 **Mode Déplacement Actif**")
                    st.markdown(f"Où voulez-vous déplacer **{client_concerne['client']}** ?")
                    st.info("👉 Cliquez directement sur une case verte 🟢 de la carte pour l'y transférer.")
                    if st.button("❌ Annuler le déplacement", use_container_width=True):
                        st.session_state.moving_client_idx = None
                        st.rerun()
                
                # CAS B : L'UTILISATEUR A CLIQUÉ SUR UNE CASE
                elif st.session_state.resa_spot_sel:
                    id_sel = st.session_state.resa_spot_sel
                    
                    # SI LA CASE EST OCCUPÉE -> ON PROPOSE LE CHANGEMENT DIRECT
                    if id_sel in emplacements_pris:
                        info_occupant = emplacements_pris[id_sel]
                        client_r = resas_du_jour[info_occupant["index"]]
                        
                        st.error(f"🔴 Place **{id_sel}** : **{info_occupant['nom']}**")
                        st.caption(f"🪑 {client_r['transats']} transats | 📍 Préf: {client_r['preference']}")
                        
                        # LE BOUTON MAGIQUE QUE TU VOULAIS :
                        if st.button("🔄 Déplacer ce client vers une autre place", type="primary", use_container_width=True):
                            st.session_state.moving_client_idx = info_occupant["index"]
                            st.session_state.resa_spot_sel = None
                            st.rerun()
                            
                        if st.button("🔓 Retirer de cette place (remettre en attente)", type="secondary", use_container_width=True):
                            client_r["est_place"] = False
                            client_r["emplacement"] = None
                            st.session_state.resa_spot_sel = None
                            st.rerun()
                            
                    # SI LA CASE EST LIBRE -> LISTE CLASSIQUE DES GENS EN ATTENTE
                    else:
                        st.success(f"🎯 **Attribuer la place {id_sel} :**")
                        resas_en_attente = [r for r in resas_du_jour if not r.get("est_place", False)]
                        
                        if not resas_en_attente:
                            st.info("Aucun client en attente pour ce jour.")
                        else:
                            for i, r in enumerate(resas_du_jour):
                                if not r.get("est_place", False):
                                    label_client = f"👤 {r['client']} ({r['transats']} tr.) \n 📍 Préf: {r['preference']}"
                                    if st.button(label_client, use_container_width=True, key=f"set_{date_choisie}_{i}"):
                                        r["est_place"] = True
                                        r["emplacement"] = id_sel
                                        st.session_state.resa_spot_sel = None
                                        st.rerun()
                else:
                    st.info("💡 Cliquez sur une place pour commencer.\n\nPour déplacer un client : cliquez sur sa place rouge 🔴 puis sur 'Déplacer'.")
                
                st.write("---")
                if st.button("🚪 Fermer et valider le plan", type="primary", use_container_width=True):
                    st.session_state.show_modal_placement = False
                    st.session_state.moving_client_idx = None
                    st.session_state.resa_spot_sel = None
                    st.rerun()
        # ------------------------------------------------------------------

        if st.session_state.show_modal_placement:
            modal_placement(date_consult_str)

        st.write("---")
        col_form, col_liste = st.columns([1, 2])

        # 2. PARTIE NOUVELLE RÉSERVATION
        with col_form:
            st.markdown("#### ➕ Nouvelle Réservation")
            with st.container(border=True):
                nom_resa = st.text_input("Nom du client :", key="form_nom")
                tel_resa = st.text_input("Téléphone :", key="form_tel")
                nb_t_resa = st.number_input("Nombre de transats :", min_value=1, max_value=10, value=2, key="form_nb")
                pref_resa = st.selectbox("Préférence :", [
                "Peu importe", "1ère Ligne impératif", "Sur un angle", "Proche de l'allée"
                ], key="form_pref")
                
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

        # 3. LISTE DES PERSONNES QUI ONT RÉSERVÉ
        with col_liste:
            st.markdown(f"#### 📋 Liste des réservations du **{date_consult_str}**")
            
            if st.button(f"🗺️ Placer les clients sur la carte du {date_consult_str}", use_container_width=True):
                st.session_state.show_modal_placement = True
                st.session_state.resa_spot_sel = None
                st.session_state.moving_client_idx = None
                st.rerun()
                
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
# ==========================================
    # MODULE : RÉCAPITULATIF JOURNALIER & PLAN
    # ==========================================
    elif page == "📊 Récap Journalier":
        st.markdown("<h3 style='color: #0f766e; text-align: center;'>📊 RÉCAPITULATIF & PLAN DE LA JOURNÉE</h3>", unsafe_allow_html=True)
        st.write("---")

        # 1. Choix du jour
        st.markdown("### 📅 Sélectionner la date à consulter")
        date_recap = st.date_input("Choisir un jour :", datetime.now().date(), key="date_recap_main")
        date_recap_str = date_recap.strftime("%d/%m/%Y")

        # Récupération des données du jour
        resas_du_jour = st.session_state.reservations.get(date_recap_str, [])
        
        # Extraction et calculs des stats
        emplacements_pris = {}
        total_transats_occupes = 0
        
        for r in resas_du_jour:
            if r.get("est_place") and r.get("emplacement"):
                emplacements_pris[r["emplacement"]] = r
                total_transats_occupes += r["transats"]

        # --- BARRE DE STATISTIQUES ---
        st.markdown("#### 📈 Chiffres clés du jour")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Réservations", len(resas_du_jour))
        with col2:
            st.metric("Clients Placés", len(emplacements_pris))
        with col3:
            # Affichage basé sur la capacité totale de 140 transats
            st.metric("Transats Occupés", f"{total_transats_occupes} / 140")

        st.write("---")

        # --- 2. VUE SUR LE PLAN DE LA PLAGE ---
        st.markdown(f"### 🗺️ Plan d'occupation du **{date_recap_str}**")
        st.caption("🟢 Libre | 🔴 Occupé (Passez la souris sur une case rouge pour voir le nom du client)")

        # Reconstruction visuelle de la grille (7 lignes x 10 colonnes avec allée)
        for l in range(1, 8):
            cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
            
            # Groupes de gauche (1 à 5)
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                if id_c in emplacements_pris:
                    info_c = emplacements_pris[id_c]
                    cols[g-1].button(
                        f"🔴\n{l}-{g}", 
                        key=f"rec_{id_c}", 
                        help=f"👤 Client : {info_c['client']}\n🪑 Transats : {info_c['transats']}\n📞 Tél : {info_c['telephone']}"
                    )
                else:
                    cols[g-1].button(f"🟢\n{l}-{g}", key=f"rec_{id_c}", help="Emplacement Libre")
                    
            # Allée centrale
            with cols[5]:
                st.markdown("<div style='text-align:center; color:#cbd5e1; font-weight:bold; padding-top:10px;'>|</div>", unsafe_allow_html=True)
                
            # Groupes de droite (6 à 10)
            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                if id_c in emplacements_pris:
                    info_c = emplacements_pris[id_c]
                    cols[g].button(
                        f"🔴\n{l}-{g}", 
                        key=f"rec_{id_c}", 
                        help=f"👤 Client : {info_c['client']}\n🪑 Transats : {info_c['transats']}\n📞 Tél : {info_c['telephone']}"
                    )
                else:
                    cols[g].button(f"🟢\n{l}-{g}", key=f"rec_{id_c}", help="Emplacement Libre")

        st.write("---")

        # --- 3. TABLEAUX RÉCAPITULATIFS EN BAS DE PAGE ---
        st.markdown("### 📋 Listing complet de la journée")
        
        if not resas_du_jour:
            st.info(f"Aucune réservation ou historique pour le {date_recap_str}.")
        else:
            # Séparation pour lisibilité
            clients_installes = [r for r in resas_du_jour if r.get("est_place")]
            clients_attente = [r for r in resas_du_jour if not r.get("est_place")]
            
            # Tableau des personnes placées
            if clients_installes:
                st.markdown("#### ✅ Emplacements attribués")
                tableau_places = []
                for r in clients_installes:
                    tableau_places.append({
                        "📍 Place": r["emplacement"],
                        "👤 Nom Client": r["client"],
                        "🪑 Nb Transats": r["transats"],
                        "📞 Téléphone": r["telephone"],
                        "🎯 Préférence": r["preference"]
                    })
                # Tri automatique par numéro d'emplacement pour que ce soit propre
                tableau_places = sorted(tableau_places, key=lambda x: x["📍 Place"])
                st.table(tableau_places)
                
            # Tableau des personnes pas encore placées (au cas où)
            if clients_attente:
                st.markdown("#### ⏳ Réservations en attente de placement pour ce jour")
                tableau_attente = []
                for r in clients_attente:
                    tableau_attente.append({
                        "👤 Nom Client": r["client"],
                        "🪑 Nb Transats": r["transats"],
                        "📞 Téléphone": r["telephone"],
                        "🎯 Préférence": r["preference"]
                    })
                st.table(tableau_attente)
