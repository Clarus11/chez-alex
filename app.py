# ==============================================================================
# PARTIE 1 : CONFIGURATION, SÉCURITÉ ET FONCTIONS LOGIQUES
# ==============================================================================
import streamlit as st
from supabase import create_client
from datetime import datetime, date
import traceback

# 1. FALLBACK RERUN (Pour éviter les crashs de rafraîchissement)
def safe_rerun():
    try:
        if hasattr(st, "experimental_rerun") and callable(st.experimental_rerun):
            return st.experimental_rerun()
    except Exception:
        pass
    try:
        if hasattr(st, "rerun") and callable(st.rerun):
            return st.rerun()
    except Exception:
        pass
    st.session_state["_force_rerun_flag"] = not st.session_state.get("_force_rerun_flag", False)

# 2. GESTION DES ERREURS
def safe_print_exception(prefix="Erreur"):
    st.error(f"{prefix} — voir logs pour la trace complète.")
    print(prefix)
    traceback.print_exc()

# 3. CALCULS DES TARIFS AUTOMATIQUES
def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    try:
        t1 = datetime.strptime(heure_arr, "%H:%M")
        t2 = datetime.strptime(heure_dep, "%H:%M")
        diff = t2 - t1
        minutes = diff.total_seconds() / 60
        if minutes < 0:
            minutes = 0
        heures = minutes / 60
        
        # Tarification dégressive : 6€/h la première heure, puis 4€/h
        if heures <= 0:
            prix_par_transat = 0
        elif heures <= 1:
            prix_par_transat = heures * 6
        else:
            prix_par_transat = 6 + (heures - 1) * 4
            
        return round(prix_par_transat * nb_transats, 2)
    except Exception:
        return 0.0

# 4. CONFIGURATION DE LA PAGE & DESIGN CSS (Chez Alex)
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    /* Style général et fond de page */
    .stApp { background-color: #fdfaf3; }
    
    /* Alignement parfait de la grille des transats */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* Boutons de la grille des transats */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: bold !important;
        padding: 6px 10px !important;
        width: 100% !important;
        transition: transform 0.1s ease;
    }
    .stButton > button:active { transform: scale(0.95); }
    </style>
    """, unsafe_allow_html=True)

# 5. INITIALISATION DES CLIENTS ET CONNEXION SUPABASE
if "supabase_ready" not in st.session_state:
    st.session_state.supabase_ready = False

try:
    url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key:
        supabase = create_client(url, key)
        st.session_state.supabase_ready = True
    else:
        st.warning("Secrets Supabase manquants. Mode simulation activé.")
except Exception as e:
    st.warning(f"Impossible de se connecter à Supabase : {e}. Mode simulation activé.")

# 6. INITIALISATION DES DONNÉES EN MÉMOIRE VOLATILE (Si Supabase absent)
if "local_reservations" not in st.session_state:
    st.session_state.local_reservations = [
        {"id": 1, "client": "Famille Martin", "telephone": "0601020304", "transats": 2, "preference": "Ligne A", "emplacement": "A3", "est_place": True, "date_resa": str(date.today()), "statut": "Confirmé", "heure_arrivee": "10:00", "heure_depart": "18:00", "montant": 68.0, "notes": ""},
        {"id": 2, "client": "Lucas Bernard", "telephone": "0611223344", "transats": 1, "preference": "Ombre", "emplacement": "", "est_place": False, "date_resa": str(date.today()), "statut": "Confirmé", "heure_arrivee": "14:00", "heure_depart": "17:00", "montant": 14.0, "notes": "Proche bord de l'eau"}
    ]

if "stocks" not in st.session_state:
    st.session_state.stocks = {"Coca-Cola": 45, "Perrier": 30, "Ice Tea": 50, "Eau Minérale": 80, "Bière blonde": 60, "Glaces (Magnum)": 25, "Chips": 40}

if "pedalos" not in st.session_state:
    st.session_state.pedalos = {str(i): {"statut": "Disponible", "heure_depart": "", "duree": "", "client": ""} for i in range(1, 6)}

# 7. FONCTIONS DE CHARGEMENT ET SAUVEGARDE DES RÉSERVATIONS
def charger_reservations(date_cible):
    if st.session_state.supabase_ready:
        try:
            res = supabase.table("reservations").select("*").eq("date_resa", str(date_cible)).execute()
            return res.data or []
        except Exception:
            safe_print_exception("Erreur lors de la récupération des données")
            return [r for r in st.session_state.local_reservations if r["date_resa"] == str(date_cible)]
    else:
        return [r for r in st.session_state.local_reservations if r["date_resa"] == str(date_cible)]

def sauvegarder_reservation(data):
    if st.session_state.supabase_ready:
        try:
            if "id" in data and data["id"]:
                supabase.table("reservations").update(data).eq("id", data["id"]).execute()
            else:
                supabase.table("reservations").insert(data).execute()
        except Exception:
            safe_print_exception("Erreur lors de la sauvegarde")
    else:
        if "id" in data and data["id"]:
            for i, r in enumerate(st.session_state.local_reservations):
                if r["id"] == data["id"]:
                    st.session_state.local_reservations[i] = data
        else:
            data["id"] = len(st.session_state.local_reservations) + 1
            st.session_state.local_reservations.append(data)

def supprimer_reservation_db(id_resa):
    if st.session_state.supabase_ready:
        try:
            supabase.table("reservations").delete().eq("id", id_resa).execute()
        except Exception:
            safe_print_exception("Erreur lors de la suppression")
    else:
        st.session_state.local_reservations = [r for r in st.session_state.local_reservations if r["id"] != id_resa]

# 8. SYSTÈME DE SÉCURITÉ & AUTHENTIFICATION (Vérifié et validé)
if "autorise" not in st.session_state:
    st.session_state.autorise = False

mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Équipe</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        mdp = st.text_input("Mot de passe d'accès :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary"):
            if mdp == mdp_secret:
                st.session_state.autorise = True
                safe_rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    st.stop()

# Si l'utilisateur arrive ici, c'est qu'il est connecté. Le code continue en Partie 2...
# ==============================================================================
# PARTIE 2 : BARRE DE NAVIGATION ET AFFICHAGE DES PAGES D'APPLICATION
# ==============================================================================

# 1. BARRE DE NAVIGATION LATÉRALE
with st.sidebar:
    st.markdown("<h2 style='color: #854d0e; text-align: center;'>🏖️ Chez Alex</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #a16207;'>Saison 2026 — Équipe</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Choix de la date de travail
    date_travail = st.date_input("📅 Date de travail :", date.today())
    
    # Menu de navigation principal
    page = st.radio(
        "🗂️ Menu principal :",
        ["🏖️ Plan de la plage", "📝 Réservations du jour", "🛶 Pédalos", "🍹 Stocks & Conso", "📊 Fin de journée"]
    )
    
    st.write("---")
    # Indicateur de connexion à la base de données
    if st.session_state.supabase_ready:
        st.success("⚡ Connecté à Supabase")
    else:
        st.warning("⚠️ Mode local temporaire")

# Chargement instantané des réservations pour la date sélectionnée
resas_du_jour = charger_reservations(date_travail)

# ==============================================================================
# PAGE 1 : 🏖️ PLAN DE LA PLAGE
# ==============================================================================
if page == "🏖️ Plan de la plage":
    st.markdown(f"### 🏖️ Plan Interactif de la Plage — {date_travail.strftime('%d/%m/%Y')}")
    st.write("Visualisation des transats et attribution en direct.")

    # Cartographie de l'occupation actuelle des transats
    occupation_transats = {}
    for r in resas_du_jour:
        if r.get("est_place") and r.get("emplacement"):
            # Un client peut réserver plusieurs places séparées par des virgules (ex: A1,A2)
            places = [p.strip() for p in str(r["emplacement"]).split(",") if p.strip()]
            for p in places:
                occupation_transats[p] = r

    # Liste d'attente pour le placement
    clients_en_attente = [r for r in resas_du_jour if not r.get("est_place")]

    if clients_en_attente:
        with st.expander(f"⚠️ Clients en attente de placement ({len(clients_en_attente)})", expanded=True):
            for r in clients_en_attente:
                col_c1, col_c2, col_c3 = st.columns([3, 2, 2])
                with col_c1:
                    st.write(f"👤 **{r['client']}** ({r['transats']} transat(s) — Préf: {r.get('preference', 'Aucune')})")
                with col_c2:
                    emplacement_choisi = st.text_input("Attribuer place(s) (ex: A1, A2) :", key=f"place_input_{r['id']}")
                with col_c3:
                    if st.button("Installer ✅", key=f"install_btn_{r['id']}", type="primary"):
                        if emplacement_choisi.strip():
                            r["emplacement"] = emplacement_choisi.strip()
                            r["est_place"] = True
                            sauvegarder_reservation(r)
                            st.success(f"{r['client']} installé en {emplacement_choisi} !")
                            safe_rerun()
                        else:
                            st.error("Indiquez un numéro.")

    st.write("---")
    
    # Génération graphique de la grille des transats (Lignes A à E, 10 transats par ligne)
    lignes = ["A", "B", "C", "D", "E"]
    for l in lignes:
        st.markdown(f"**Ligne {l}**")
        colonnes_grille = st.columns(10)
        for num in range(1, 11):
            nom_place = f"{l}{num}"
            with colonnes_grille[num - 1]:
                if nom_place in occupation_transats:
                    client_sur_transat = occupation_transats[nom_place]
                    # Transat occupé (Bouton Rouge)
                    if st.button(f"🔴\n{nom_place}", key=f"btn_grid_{nom_place}"):
                        st.info(f"**Emplacement {nom_place}**\n\n👤 Client : {client_sur_transat['client']}\n\n📞 Tél : {client_sur_transat['telephone']}\n\n⏰ Horaires : {client_sur_transat['heure_arrivee']} - {client_sur_transat['heure_depart']}")
                else:
                    # Transat libre (Bouton Blanc/Neutre)
                    if st.button(f"⚪\n{nom_place}", key=f"btn_grid_{nom_place}"):
                        st.success(f"L'emplacement {nom_place} est actuellement libre.")

# ==============================================================================
# PAGE 2 : 📝 RÉSERVATIONS DU JOUR
# ==============================================================================
elif page == "📝 Réservations du jour":
    st.markdown(f"### 📝 Registre des Réservations — {date_travail.strftime('%d/%m/%Y')}")
    
    # Formulaire d'ajout rapide d'une nouvelle réservation
    with st.expander("➕ Enregistrer une nouvelle réservation", expanded=False):
        with st.form("form_nouvelle_resa"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nom_client = st.text_input("Nom du client * :")
                telephone = st.text_input("Numéro de téléphone :")
                nb_transats = st.number_input("Nombre de transats :", min_value=1, max_value=20, value=2)
                preference = st.text_input("Préférence d'emplacement (ex: Ligne A, Ombre) :")
            with col_f2:
                heure_arr = st.text_input("Heure d'arrivée (HH:MM) :", value="10:00")
                heure_dep = st.text_input("Heure de départ (HH:MM) :", value="18:00")
                notes = st.text_area("Notes particulières :")
            
            bouton_valider = st.form_submit_button("Sauvegarder la réservation 💾", type="primary")
            
            if bouton_valider:
                if not nom_client.strip():
                    st.error("Le nom du client est obligatoire.")
                else:
                    nouveau_montant = calculer_tarif_heures(heure_arr, heure_dep, nb_transats)
                    nouvelle_resa = {
                        "client": nom_client.strip(),
                        "telephone": telephone.strip(),
                        "transats": int(nb_transats),
                        "preference": preference.strip(),
                        "emplacement": "",
                        "est_place": False,
                        "date_resa": str(date_travail),
                        "statut": "Confirmé",
                        "heure_arrivee": heure_arr,
                        "heure_depart": heure_dep,
                        "montant": nouveau_montant,
                        "notes": notes.strip()
                    }
                    sauvegarder_reservation(nouvelle_resa)
                    st.success(f"Réservation enregistrée pour {nom_client} ! (Estimation : {nouveau_montant}€)")
                    safe_rerun()

    # Affichage de la liste sous forme de tableau propre
    st.write("---")
    if not resas_du_jour:
        st.info("Aucune réservation enregistrée pour cette journée.")
    else:
        for r in resas_du_jour:
            statut_badge = "✅ Installé" if r.get("est_place") else "⏳ En attente"
            place_badge = f"📍 Place : {r['emplacement']}" if r.get("est_place") else "❌ Non placé"
            
            with st.container():
                col_r1, col_r2, col_r3 = st.columns([4, 3, 2])
                with col_r1:
                    st.markdown(f"**👤 {r['client']}** — {r['transats']} transat(s) ({r['heure_arrivee']} - {r['heure_depart']})")
                    if r.get("notes"): st.caption(f"📝 *Note : {r['notes']}*")
                with col_r2:
                    st.write(f"{statut_badge} | {place_badge} | 💰 **{r['montant']} €**")
                with col_r3:
                    # Bouton d'annulation/suppression
                    if st.button("Annuler 🗑️", key=f"del_resa_{r['id']}"):
                        supprimer_reservation_db(r["id"])
                        st.success("Réservation supprimée.")
                        safe_rerun()
            st.write("<hr style='margin:0.5em 0; border-color:#eee;' />", unsafe_allow_html=True)

# ==============================================================================
# PAGE 3 : 🛶 PÉDALOS
# ==============================================================================
elif page == "🛶 Pédalos":
    st.markdown("### 🛶 Suivi de la Flotte de Pédalos")
    st.write("Gestion des départs et des retours à la cabane nautique.")

    for num_p, info_p in st.session_state.pedalos.items():
        col_p1, col_p2, col_p3 = st.columns([2, 3, 2])
        with col_p1:
            st.markdown(f"#### 🛶 Pédalo N°{num_p}")
            if info_p["statut"] == "Disponible":
                st.markdown("<span style='color:green; font-weight:bold;'>🟢 Disponible</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red; font-weight:bold;'>🔴 En mer ({info_p['duree']})</span>", unsafe_allow_html=True)
        
        with col_p2:
            if info_p["statut"] == "Disponible":
                client_p = st.text_input("Client :", key=f"client_p_{num_p}")
                duree_p = st.selectbox("Durée prévue :", ["30 min", "1h", "2h"], key=f"duree_p_{num_p}")
            else:
                st.write(f"👤 Équipage : **{info_p['client']}**")
                st.write(f"⏰ Parti à : {info_p['heure_depart']}")
        
        with col_p3:
            if info_p["statut"] == "Disponible":
                if st.button("Louer 🚀", key=f"louer_p_{num_p}", type="primary"):
                    if client_p.strip():
                        st.session_state.pedalos[num_p] = {
                            "statut": "Loué",
                            "heure_depart": datetime.now().strftime("%H:%M"),
                            "duree": duree_p,
                            "client": client_p.strip()
                        }
                        st.success(f"Pédalo N°{num_p} a pris la mer !")
                        safe_rerun()
                    else:
                        st.error("Entrez le nom du client.")
            else:
                if st.button("Retour Cabane ⚓", key=f"retour_p_{num_p}"):
                    st.session_state.pedalos[num_p] = {"statut": "Disponible", "heure_depart": "", "duree": "", "client": ""}
                    st.success(f"Pédalo N°{num_p} nettoyé et de retour !")
                    safe_rerun()
        st.write("---")

# ==============================================================================
# PAGE 4 : 🍹 STOCKS & CONSO
# ==============================================================================
elif page == "🍹 Stocks & Conso":
    st.markdown("### 🍹 Inventaire du Bar de Plage")
    st.write("Mise à jour rapide des ventes et réapprovisionnements.")
    
    st.write(" ")
    for produit, quantite in st.session_state.stocks.items():
        col_item, col_qt, col_actions = st.columns([3, 1, 3])
        
        with col_item:
            st.markdown(f"##### 🍹 {produit}")
        with col_qt:
            # Alerte si le stock devient trop bas
            if quantite <= 10:
                st.markdown(f"<span style='color:red; font-weight:bold;'>{quantite} (BAS)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{quantite}**")
        with col_actions:
            c_m1, c_p1, c_p10 = st.columns(3)
            with c_m1:
                if st.button("➖ 1", key=f"m1_{produit}"):
                    if st.session_state.stocks[produit] > 0:
                        st.session_state.stocks[produit] -= 1
                        safe_rerun()
            with c_p1:
                if st.button("➕ 1", key=f"p1_{produit}"):
                    st.session_state.stocks[produit] += 1
                    safe_rerun()
            with c_p10:
                if st.button("➕ 10", key=f"p10_{produit}"):
                    st.session_state.stocks[produit] += 10
                    safe_rerun()
        st.write("<hr style='margin:0.3em 0; border-color:#eee;' />", unsafe_allow_html=True)

# ==============================================================================
# PAGE 5 : 📊 FIN DE JOURNÉE
# ==============================================================================
elif page == "📊 Fin de journée":
    st.markdown(f"### 📊 Bilan du Jour — {date_travail.strftime('%d/%m/%Y')}")
    
    # Calcul des indicateurs clés financiers
    total_ca_estime = sum(float(r.get("montant", 0.0)) for r in resas_du_jour)
    total_transats_loues = sum(int(r.get("transats", 0)) for r in resas_du_jour if r.get("est_place"))
    total_clients = len(resas_du_jour)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("💰 Chiffre d'Affaires Plage Estimé", f"{total_ca_estime:.2f} €")
    with col_m2:
        st.metric("🪑 Total Transats Occupés", f"{total_transats_loues} / 50")
    with col_m3:
        st.metric("👥 Dossiers Clients Traités", total_clients)

    st.write("---")
    st.markdown("#### ✅ Récapitulatif des emplacements clôturés")
    
    if not resas_du_jour:
        st.info("Aucune activité aujourd'hui pour générer le récapitulatif.")
    else:
        tableau_recap = []
        for r in resas_du_jour:
            tableau_recap.append({
                "Client": r["client"],
                "Transats": r["transats"],
                "Emplacement": r["emplacement"] if r.get("est_place") else "Non placé",
                "Horaires": f"{r['heure_arrivee']} - {r['heure_depart']}",
                "Montant dû": f"{r['montant']} €"
            })
        st.table(tableau_recap)
