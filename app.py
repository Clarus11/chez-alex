import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE (THÈME SABLE)
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Fond de l'application */
    .stApp { background-color: #fdfaf3; }
    
    /* Alignement horizontal du plan de plage */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* Boutons des emplacements */
    .stButton > button {
        width: 100% !important;
        height: 60px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    
    /* Allée centrale */
    .allee-verticale {
        background-color: #fef08a;
        color: #854d0e;
        font-weight: bold;
        text-align: center;
        padding: 15px 2px;
        border-radius: 4px;
        font-size: 10px;
        writing-mode: vertical-lr;
        transform: rotate(180deg);
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Style du bloc Total Encaissé */
    .total-display {
        background-color: #1e3a8a; color: white; padding: 15px; 
        border-radius: 10px; text-align: center; font-size: 24px; 
        font-weight: bold; margin-top: 15px; margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SÉCURITÉ (MOT DE PASSE)
# ==========================================
if "autorise" not in st.session_state:
    st.session_state.autorise = False

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Accès Équipe</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Mot de passe :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary"):
            if mdp == st.secrets["password"]:  # Mot de passe vérifié
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
else:
    # ==========================================
    # 3. INITIALISATION DE TOUTES LES DONNÉES
    # ==========================================
    # La plage (140 transats / 70 groupes)
    if "plage" not in st.session_state:
        st.session_state.plage = {}
        for l in range(1, 8):
            for g in range(1, 11):
                id_c = f"L{l}-G{g}"
                st.session_state.plage[id_c] = {
                    "statut": "Libre", "client": "", "heure_arrivee": "", "heure_fin": "",
                    "nb_transats": 2, "forfait": "Journée (15€)", "prix_transats": 0.0, "conso": 0.0,
                    "historique_conso": []
                }
    
    # Finances et Stocks
    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    if "stocks" not in st.session_state: 
        st.session_state.stocks = {"Soda & Eau": 100, "Glace": 50, "Snack": 30}
    
    # To-Do List (Notes)
    if "notes" not in st.session_state: st.session_state.notes = []
    
    # Gestion des pop-ups
    if "groupe_selectionne" not in st.session_state: st.session_state.groupe_selectionne = None

    # ==========================================
    # 4. MENU LATÉRAL DE NAVIGATION
    # ==========================================
    with st.sidebar:
        st.markdown("<h2 style='color: #854d0e; text-align: center;'>CHEZ ALEX</h2>", unsafe_allow_html=True)
        st.write("---")
        page = st.radio("Navigation :", [
            "🏖️ Plan de la plage", 
            "📝 Notes (To-Do List)",
            "📦 Stocks & Frigos", 
            "📊 Chiffre d'Affaires",
            "📅 Réservations", 
            "🚣 Pédalos"
        ])
        st.write("---")
        if st.button("🔒 Verrouiller l'app"):
            st.session_state.autorise = False
            st.rerun()

    # ==========================================
    # PAGE 1 : PLAN DE LA PLAGE ET ENCAISSEMENT
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
        st.write("")

        # Génération de la grille 7x10
        for l in range(1, 8):
            st.caption(f"Ligne {l}")
            cols = st.columns([1, 1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1])
            
            # GAUCHE (1 à 5)
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g-1].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

            # ALLÉE CENTRALE
            with cols[5]: st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

            # DROITE (6 à 10)
            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

        # ------------------------------------------
        # POP-UP DE GESTION DU TRANSAT (LE CŒUR DU SYSTÈME)
        # ------------------------------------------
        if st.session_state.groupe_selectionne:
            @st.dialog("Gestion de l'emplacement")
            def gerer_place(id_sel):
                info = st.session_state.plage[id_sel]
                num_l, num_g = id_sel.replace("L","").split("-G")
                st.markdown(f"#### Emplacement **{num_l}-{num_g}**")
                
                # SI LA PLACE EST LIBRE -> INSTALLATION
                if info["statut"] == "Libre":
                    nom = st.text_input("👤 Nom du client :")
                    nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=2)
                    
                    # Tes 3 tarifs !
                    forfait = st.radio("💰 Forfait choisi :", ["Journée (15€)", "Demi-journée (12€)", "2 heures (7€)"])
                    
                    c1, c2 = st.columns(2)
                    h_a = c1.text_input("⏰ Arrivée :", datetime.now().strftime("%H:%M"))
                    h_f = c2.text_input("⏳ Fin prévue :", "18:00")
                    
                    if st.button("✅ Installer le client", type="primary"):
                        if nom:
                            # Détermination du prix unitaire
                            prix_u = 15.0 if "Journée" in forfait else (12.0 if "Demi" in forfait else 7.0)
                            total_transats = nb_t * prix_u
                            
                            st.session_state.plage[id_sel].update({
                                "statut": "Occupé", "client": nom, "nb_transats": nb_t,
                                "forfait": forfait, "prix_transats": total_transats,
                                "heure_arrivee": h_a, "heure_fin": h_f, "conso": 0.0, "historique_conso": []
                            })
                            st.session_state.groupe_selectionne = None
                            st.rerun()
                        else:
                            st.error("Veuillez entrer un nom.")

                # SI LA PLACE EST OCCUPÉE -> SERVICE ET ENCAISSEMENT
                else:
                    st.info(f"👤 **{info['client']}** | {info['nb_transats']} transat(s) en {info['forfait']}")
                    st.caption(f"⏰ Arrivée : {info['heure_arrivee']} | Départ prévu : {info['heure_fin']}")
                    
                    # Ajout de consommations (Baisse les stocks automatiquement)
                    st.write("🛒 **Ajouter une consommation :**")
                    col_b1, col_b2, col_b3 = st.columns(3)
                    
                    if col_b1.button("+ Soda/Eau (4.5€)"):
                        st.session_state.plage[id_sel]["conso"] += 4.5
                        st.session_state.plage[id_sel]["historique_conso"].append("Soda/Eau")
                        st.session_state.stocks["Soda & Eau"] -= 1
                        st.rerun()
                        
                    if col_b2.button("+ Glace (5€)"):
                        st.session_state.plage[id_sel]["conso"] += 5.0
                        st.session_state.plage[id_sel]["historique_conso"].append("Glace")
                        st.session_state.stocks["Glace"] -= 1
                        st.rerun()
                        
                    if col_b3.button("+ Snack (7€)"):
                        st.session_state.plage[id_sel]["conso"] += 7.0
                        st.session_state.plage[id_sel]["historique_conso"].append("Snack")
                        st.session_state.stocks["Snack"] -= 1
                        st.rerun()

                    # Affichage des consos prises
                    if info["historique_conso"]:
                        st.write(f"📝 *Ardoise : {', '.join(info['historique_conso'])}*")

                    # Calcul du Total parfait
                    total_a_payer = info["prix_transats"] + info["conso"]
                    st.markdown(f"<div class='total-display'>TOTAL À ENCAISSER : {total_a_payer:.2f} €</div>", unsafe_allow_html=True)
                    
                    # Boutons d'action finaux
                    col_act1, col_act2 = st.columns(2)
                    if col_act1.button("💵 ENCAISSER & LIBÉRER", type="primary"):
                        # Ajoute l'argent au CA de la journée
                        st.session_state.ca_jour += total_a_payer
                        # Remet la place à zéro
                        st.session_state.plage[id_sel].update({
                            "statut": "Libre", "client": "", "heure_arrivee": "", "heure_fin": "",
                            "prix_transats": 0.0, "conso": 0.0, "historique_conso": []
                        })
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                        
                    if col_act2.button("Fermer la fiche"):
                        st.session_state.groupe_selectionne = None
                        st.rerun()

            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # PAGE 2 : NOTES ET TO-DO LIST (Cases à cocher)
    # ==========================================
    elif page == "📝 Notes (To-Do List)":
        st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
        st.write("Ajoute tes idées ou le matériel à ramener. Coche la case une fois que c'est fait !")
        
        # Ajouter une note
        col_note, col_btn = st.columns([4, 1])
        nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Ramener 2 parasols Ligne 4")
        if col_btn.button("Ajouter"):
            if nouvelle_note:
                st.session_state.notes.append(nouvelle_note)
                st.rerun()

        st.write("---")
        
        # Afficher les notes avec cases à cocher
        if len(st.session_state.notes) == 0:
            st.success("Toutes les tâches sont terminées ! 😎")
        else:
            notes_a_supprimer = []
            for i, note in enumerate(st.session_state.notes):
                # Si on coche la case, la tâche est ajoutée à la liste de suppression
                fait = st.checkbox(note, key=f"note_{i}")
                if fait:
                    notes_a_supprimer.append(i)
            
            # Suppression effective après validation
            if notes_a_supprimer:
                for i in reversed(notes_a_supprimer): # On supprime à l'envers pour ne pas décaler l'index
                    st.session_state.notes.pop(i)
                st.rerun()

    # ==========================================
    # PAGE 3 : STOCKS & FRIGOS
    # ==========================================
    elif page == "📦 Stocks & Frigos":
        st.markdown("<h3 style='color: #854d0e;'>📦 État des Stocks</h3>", unsafe_allow_html=True)
        st.info("Ces stocks baissent tout seuls quand tu ajoutes une conso à un client sur la plage.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🥤 Sodas & Eaux", f"{st.session_state.stocks['Soda & Eau']} unités")
        c2.metric("🍦 Glaces", f"{st.session_state.stocks['Glace']} unités")
        c3.metric("🥪 Snacks", f"{st.session_state.stocks['Snack']} unités")
        
        st.write("---")
        st.subheader("Réassort (Les livreurs sont passés)")
        if st.button("Remplir les Frigos (+50 Sodas/Eaux)"):
            st.session_state.stocks["Soda & Eau"] += 50
            st.rerun()

    # ==========================================
    # PAGE 4 : CHIFFRE D'AFFAIRES
    # ==========================================
    elif page == "📊 Chiffre d'Affaires":
        st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
        st.metric("Total Encaissé Aujourd'hui", f"{st.session_state.ca_jour:.2f} €")
        st.success("Ce montant augmente automatiquement dès que tu cliques sur 'ENCAISSER & LIBÉRER' sur le plan de plage.")

    # ==========================================
    # PAGES EN ATTENTE (Résas & Pédalos)
    # ==========================================
    elif page in ["📅 Réservations", "🚣 Pédalos"]:
        st.markdown(f"<h3 style='color: #854d0e;'>{page}</h3>", unsafe_allow_html=True)
        st.warning("Cette section sera développée à la prochaine étape !")
