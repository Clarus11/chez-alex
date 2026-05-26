import streamlit as st
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET STYLE (THÈME SABLE & PLAGE)
# ==========================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Fond général de l'application */
    .stApp { background-color: #fdfaf3; }
    
    /* Alignement horizontal du plan de plage */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* Boutons des emplacements de transats */
    .stButton > button {
        width: 100% !important;
        height: 60px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    
    /* Style de l'allée centrale */
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
    
    /* Blocs de synthèse financière */
    .total-display {
        background-color: #1e3a8a; color: white; padding: 15px; 
        border-radius: 10px; text-align: center; font-size: 20px; 
        font-weight: bold; margin-top: 10px; margin-bottom: 10px;
    }
    .paye-direct-display {
        background-color: #10b981; color: white; padding: 12px; 
        border-radius: 10px; text-align: center; font-size: 15px; 
        font-weight: bold; margin-top: 10px; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIQUE DE CALCUL DYNAMIQUE PAR HORAIRES
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
        
        # Application stricte de vos paliers de tarifs
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
        return 15.0 * nb_transats, 0.0, "Tarif Journée (Calcul défaut)"

# ==========================================
# 3. SÉCURITÉ D'ACCÈS
# ==========================================
if "autorise" not in st.session_state:
    st.session_state.autorise = False

# Fallback sur mot de passe par défaut si non configuré dans vos secrets GitHub
mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Accès Équipe</h2>", unsafe_allow_html=True)
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
    # 4. INITIALISATION DE LA STRUCTURE DE DONNÉES
    # ==========================================
    if "plage" not in st.session_state:
        st.session_state.plage = {}
        for l in range(1, 8):
            for g in range(1, 11):
                id_c = f"L{l}-G{g}"
                st.session_state.plage[id_c] = {
                    "statut": "Libre", 
                    "client": "", 
                    "heure_arrivee": "", 
                    "nb_transats": 2, 
                    "transats_payes": False,
                    "prix_transats_encaisse": 0.0,
                    "conso_ardoise": 0.0, 
                    "historique_conso": [],
                    "paye_direct": 0.0,
                    "historique_paye_direct": []
                }
    
    if "ca_jour" not in st.session_state: st.session_state.ca_jour = 0.0
    if "stocks" not in st.session_state: st.session_state.stocks = {"Soda & Eau": 100, "Glace": 50, "Snack": 30}
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
    # MODULES COMPLETS ET CORRIGÉS
    # ==========================================
    if page == "🏖️ Plan de la plage":
        st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
        st.write("")

        # Affichage de la plage (Grille 7 x 10)
        for l in range(1, 8):
            st.caption(f"Ligne {l}")
            cols = st.columns([1, 1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1])
            
            # Côté Gauche (Groupes 1 à 5)
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g-1].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

            # Allée centrale
            with cols[5]: st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

            # Côté Droit (Groupes 6 à 10)
            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                info = st.session_state.plage[id_c]
                label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
                if cols[g].button(label, key=id_c, type="secondary" if info["statut"] == "Libre" else "primary"):
                    st.session_state.groupe_selectionne = id_c
                    st.rerun()

        # ------------------------------------------
        # POP-UP INTELLIGENT DE GESTION DU TRANSAT
        # ------------------------------------------
        if st.session_state.groupe_selectionne:
            @st.dialog("Gestion de l'emplacement")
            def gerer_place(id_sel):
                info = st.session_state.plage[id_sel]
                num_l, num_g = id_sel.replace("L","").split("-G")
                st.markdown(f"#### Emplacement **{num_l}-{num_g}**")
                
                # --- ACTION 1 : ARRIVÉE DU CLIENT (PLUS DE CHOIX DE FORFAIT EN AMONT) ---
                if info["statut"] == "Libre":
                    nom = st.text_input("👤 Nom du client :")
                    nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=2)
                    h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"))
                    
                    if st.button("✅ Installer le client", type="primary"):
                        if nom:
                            st.session_state.plage[id_sel].update({
                                "statut": "Occupé", "client": nom, "nb_transats": nb_t,
                                "heure_arrivee": h_a, "transats_payes": False, "prix_transats_encaisse": 0.0,
                                "conso_ardoise": 0.0, "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                            })
                            st.session_state.groupe_selectionne = None
                            st.rerun()
                        else:
                            st.error("Veuillez renseigner le nom du client.")

                # --- ACTION 2 : CLIENT EN PLACE & SUIVI DES PAIEMENTS DIRECTS ---
                else:
                    st.markdown(f"👤 **{info['client']}** | 🪑 {info['nb_transats']} transat(s) | ⏰ Arrivée : {info['heure_arrivee']}")
                    
                    # Détermination du temps passé à la minute près
                    h_actuelle = datetime.now().strftime("%H:%M")
                    h_dep = st.text_input("⏳ Heure de calcul / de départ :", h_actuelle)
                    
                    frais_transats, heures_passees, libelle_tarif = calculer_tarif_heures(info["heure_arrivee"], h_dep, info["nb_transats"])
                    st.markdown(f"⏱️ *Temps cumulé : {heures_passees:.2f}h* — **{libelle_tarif}**")
                    
                    # Suivi du paiement direct du transat
                    st.write("---")
                    st.write("💰 **Règlement de la location des Transats :**")
                    if not info["transats_payes"]:
                        st.warning(f"Montant calculé : {frais_transats:.2f} €")
                        if st.button("💵 Encaisser les transats DIRECTEMENT"):
                            st.session_state.ca_jour += frais_transats
                            st.session_state.plage[id_sel]["transats_payes"] = True
                            st.session_state.plage[id_sel]["prix_transats_encaisse"] = frais_transats
                            st.rerun()
                    else:
                        st.success(f"✅ Transats payés en direct à l'installation ({info['prix_transats_encaisse']:.2f} €)")

                    # Section de choix de saisie des consommations
                    st.write("---")
                    st.write("🛒 **Ajouter une consommation (Double Option) :**")
                    
                    col_art, col_ard, col_dir = st.columns([2, 1.5, 1.5])
                    with col_art:
                        st.markdown("**🥤 Soda / Eau** (4.5€)")
                        st.markdown("**🍦 Glace** (5.0€)")
                        st.markdown("**🥪 Snack** (7.0€)")
                        
                    with col_ard:
                        if st.button("+ Ardoise", key="s_ard"):
                            st.session_state.plage[id_sel]["conso_ardoise"] += 4.5
                            st.session_state.plage[id_sel]["historique_conso"].append("Soda/Eau (Ardoise)")
                            st.session_state.stocks["Soda & Eau"] -= 1
                            st.rerun()
                        if st.button("+ Ardoise", key="g_ard"):
                            st.session_state.plage[id_sel]["conso_ardoise"] += 5.0
                            st.session_state.plage[id_sel]["historique_conso"].append("Glace (Ardoise)")
                            st.session_state.stocks["Glace"] -= 1
                            st.rerun()
                        if st.button("+ Ardoise", key="sn_ard"):
                            st.session_state.plage[id_sel]["conso_ardoise"] += 7.0
                            st.session_state.plage[id_sel]["historique_conso"].append("Snack (Ardoise)")
                            st.session_state.stocks["Snack"] -= 1
                            st.rerun()
                            
                    with col_dir:
                        if st.button("⚡ Payé Direct", key="s_dir"):
                            st.session_state.ca_jour += 4.5
                            st.session_state.plage[id_sel]["paye_direct"] += 4.5
                            st.session_state.plage[id_sel]["historique_paye_direct"].append("Soda/Eau (Espèces/CB)")
                            st.session_state.stocks["Soda & Eau"] -= 1
                            st.rerun()
                        if st.button("⚡ Payé Direct", key="g_dir"):
                            st.session_state.ca_jour += 5.0
                            st.session_state.plage[id_sel]["paye_direct"] += 5.0
                            st.session_state.plage[id_sel]["historique_paye_direct"].append("Glace (Espèces/CB)")
                            st.session_state.stocks["Glace"] -= 1
                            st.rerun()
                        if st.button("⚡ Payé Direct", key="sn_dir"):
                            st.session_state.ca_jour += 7.0
                            st.session_state.plage[id_sel]["paye_direct"] += 7.0
                            st.session_state.plage[id_sel]["historique_paye_direct"].append("Snack (Espèces/CB)")
                            st.session_state.stocks["Snack"] -= 1
                            st.rerun()

                    if info["historique_conso"]:
                        st.caption(f"📝 *Sur la note globale : {', '.join(info['historique_conso'])}*")
                    if info["historique_paye_direct"]:
                        st.caption(f"✨ *Déjà réglé en direct : {', '.join(info['historique_paye_direct'])}*")

                    # Calcul précis des restes à percevoir à la clôture
                    st.write("---")
                    transats_dus = 0.0 if info["transats_payes"] else frais_transats
                    total_du_final = transats_dus + info["conso_ardoise"]
                    
                    total_historique_paye = info["paye_direct"] + info["prix_transats_encaisse"]
                    st.markdown(f"<div class='paye-direct-display'>DÉJÀ PAYÉ EN DIRECT SUR LE TRANSAT : {total_historique_paye:.2f} €</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='total-display'>RESTE À PAYER À LA CLÔTURE : {total_du_final:.2f} €</div>", unsafe_allow_html=True)
                    
                    col_fin1, col_fin2 = st.columns(2)
                    if col_fin1.button("💵 SOLDE & LIBÉRER LE GROUPE", type="primary"):
                        st.session_state.ca_jour += total_du_final
                        st.session_state.plage[id_sel].update({
                            "statut": "Libre", "client": "", "heure_arrivee": "",
                            "transats_payes": False, "prix_transats_encaisse": 0.0,
                            "conso_ardoise": 0.0, "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                        })
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                        
                    if col_fin2.button("Fermer le dossier"):
                        st.session_state.groupe_selectionne = None
                        st.rerun()

            gerer_place(st.session_state.groupe_selectionne)

    # ==========================================
    # LES AUTRES MODULES RESTE EN PLACE CONFORMES
    # ==========================================
    elif page == "📝 Notes (To-Do List)":
        st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
        col_note, col_btn = st.columns([4, 1])
        nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Ramener 2 parasols Ligne 4")
        if col_btn.button("Ajouter"):
            if nouvelle_note:
                st.session_state.notes.append(nouvelle_note)
                st.rerun()
        st.write("---")
        if not st.session_state.notes:
            st.success("Toutes les tâches sont terminées ! 😎")
        else:
            notes_a_supprimer = []
            for i, note in enumerate(st.session_state.notes):
                if st.checkbox(note, key=f"note_{i}"):
                    notes_a_supprimer.append(i)
            if notes_a_supprimer:
                for i in reversed(notes_a_supprimer):
                    st.session_state.notes.pop(i)
                st.rerun()

    elif page == "📦 Stocks & Frigos":
        st.markdown("<h3 style='color: #854d0e;'>📦 État des Stocks</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("🥤 Sodas & Eaux", f"{st.session_state.stocks['Soda & Eau']} unités")
        c2.metric("🍦 Glaces", f"{st.session_state.stocks['Glace']} unités")
        c3.metric("🥪 Snacks", f"{st.session_state.stocks['Snack']} unités")

    elif page == "📊 Chiffre d'Affaires":
        st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
        st.metric("Total Encaissé Aujourd'hui", f"{st.session_state.ca_jour:.2f} €")

    elif page in ["📅 Réservations", "🚣 Pédalos"]:
        st.markdown(f"<h3 style='color: #854d0e;'>{page}</h3>", unsafe_allow_html=True)
        st.warning("Prêt pour le développement de ce module à la prochaine étape !")
