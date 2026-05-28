import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

# ==============================================================================
# 1. CONFIGURATION DE L'APPLICATION & INTERFACE
# ==============================================================================
st.set_page_config(page_title="Chez Alex 2026 — Gestion de Plage", page_icon="🏖️", layout="wide")

# Injection CSS pour le rendu de la grille de la plage et l'alignement responsive
st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }
    div[data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; gap: 5px !important; align-items: center !important; padding: 0 !important; }
    .stButton > button { border-radius: 6px !important; font-weight: bold !important; padding: 8px 4px !important; width: 100% !important; min-height: 60px !important; font-size: 11px !important; line-height: 1.2 !important; }
    .stButton > button:hover { transform: scale(1.02); }
    .allée-centrale { background-color: #fef08a; color: #854d0e; font-weight: bold; text-align: center; padding: 20px 1px; border-radius: 4px; font-size: 10px; writing-mode: vertical-lr; height: 60px; display: flex; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CONNEXION REELES / BACKUP SUPABASE
# ==============================================================================
if "supabase_ready" not in st.session_state:
    st.session_state.supabase_ready = False

try:
    url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key:
        supabase = create_client(url, key)
        st.session_state.supabase_ready = True
    else:
        st.warning("Mode Sauvegarde Locale Activé (Pas de clés Supabase).")
except Exception:
    st.warning("Mode Sauvegarde Locale Activé (Erreur de connexion).")

# ==============================================================================
# 3. INITIALIZATION DES STATES (Mémoire vive de l'application)
# ==============================================================================
if "local_db" not in st.session_state:
    st.session_state.local_db = []
if "place_selectionnee" not in st.session_state:
    st.session_state.place_selectionnee = None
if "pedalo_selectionne" not in st.session_state:
    st.session_state.pedalo_selectionne = None

if "stocks" not in st.session_state:
    st.session_state.stocks = {
        "Coca-Cola": 50, "Coca-Cola Zero": 50, "Orangina": 40, "Schweppes Agrume": 40,
        "Petite Eau": 100, "Grande Eau": 60, "Café / Thé": 200, "Virgin Mojito": 30, "Glace Artisanale": 45
    }

if "pedalos" not in st.session_state:
    st.session_state.pedalos = {
        str(i): {"statut": "Disponible", "heure_depart": "", "duree": "1h", "client": "", "compteur_raz": str(date.today())}
        for i in range(1, 6)
    }

TARIFS_CONSO = {
    "Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50,
    "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Virgin Mojito": 6.00, "Glace Artisanale": 3.80
}

# ==============================================================================
# 4. ENGINE DE CALCUL TARIFAIRE STRICT (15€ / 12€ / 7€)
# ==============================================================================
def calculer_tarif_plage(heure_arr, heure_dep, nb_transats):
    """Applique la tarification stricte : 2h = 7€, Demi-journée = 12€, Journée = 15€"""
    try:
        t1 = datetime.strptime(heure_arr.strip(), "%H:%M")
        t2 = datetime.strptime(heure_dep.strip(), "%H:%M")
        delta_heures = (t2 - t1).total_seconds() / 3600
        
        if delta_heures <= 0:
            return 0.0
        elif delta_heures <= 2.2: # Tolérance de 12 min incluse
            tarif_unitaire = 7.0
        elif delta_heures <= 4.5: # Demi-journée jusqu'à 4h30 de présence
            tarif_unitaire = 12.0
        else:
            tarif_unitaire = 15.0
            
        return round(tarif_unitaire * int(nb_transats), 2)
    except Exception:
        return 0.0

# ==============================================================================
# 5. SYSTÈME DE SYNCHRONISATION DES FLUX DE DONNÉES
# ==============================================================================
def charger_reservations(date_cible):
    if st.session_state.supabase_ready:
        try:
            res = supabase.table("reservations").select("*").eq("date_resa", str(date_cible)).execute()
            return res.data or []
        except Exception:
            return [r for r in st.session_state.local_db if r["date_resa"] == str(date_cible)]
    return [r for r in st.session_state.local_db if r["date_resa"] == str(date_cible)]

def sauvegarder_reservation(data):
    if st.session_state.supabase_ready:
        try:
            if "id" in data and data["id"]:
                supabase.table("reservations").update(data).eq("id", data["id"]).execute()
            else:
                res = supabase.table("reservations").insert(data).execute()
                if res.data:
                    data["id"] = res.data[0]["id"]
        except Exception as e:
            st.error(f"Erreur Supabase synchro : {e}")
    
    # Backup ou mode local systématique pour éviter les blocages de l'interface
    if "id" in data and data["id"]:
        for idx, r in enumerate(st.session_state.local_db):
            if r.get("id") == data["id"]:
                st.session_state.local_db[idx] = data
                return
    else:
        data["id"] = len(st.session_state.local_db) + 1
        st.session_state.local_db.append(data)

# ==============================================================================
# 6. DOUBLE RIDEAU DE SÉCURITÉ ACCÈS COMPTOIR
# ==============================================================================
if "autorise" not in st.session_state:
    st.session_state.autorise = False

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e; margin-top:100px;'>🏖️ CHEZ ALEX — ACCÈS COMPTOIR</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        mdp = st.text_input("Saisir le mot de passe d'administration :", type="password")
        if st.button("Valider l'ouverture du poste de contrôle 🔓", type="primary"):
            if mdp == st.secrets.get("password", "alex2026"):
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect — Accès refusé.")
    st.stop()
    # ==============================================================================
# 7. FILTRES DE NAVIGATION ET CONTRÔLE TEMPOREL
# ==============================================================================
with st.sidebar:
    st.markdown("<h2 style='color: #854d0e; text-align: center; margin-bottom:0;'>🏖️ CHEZ ALEX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:12px; color:#a16207;'>Gestionnaire de Plage v3.5 (Stable)</p>", unsafe_allow_html=True)
    st.write("---")
    date_travail = st.date_input("📆 Choisir la date d'exploitation :", date.today())
    page = st.radio("📂 Navigation Modules :", ["🏖️ Plan de la plage", "📝 Registre Réservations", "🛶 Flotte Pédalos", "🍹 Suivi Stocks"])

# Chargement dynamique des flux pour la date sélectionnée
resas_du_jour = charger_reservations(date_travail)

# ==============================================================================
# MODULE 1 : 🏖️ PLAN DE LA PLAGE (REPRODUCTION ET MAILLAGE DES 140 PLACES)
# ==============================================================================
if page == "🏖️ Plan de la plage":
    st.markdown(f"<h3 style='color: #854d0e; text-align: center;'>PLAN DIRECT DU COMPTOIR — {date_travail.strftime('%d/%m/%Y')}</h3>", unsafe_allow_html=True)

    # Cartographie temps réel de l'occupation
    occupation_transats = {}
    for r in resas_du_jour:
        if r.get("est_place") and r.get("emplacement"):
            places = [p.strip() for p in str(r["emplacement"]).split(",") if p.strip()]
            for p in places:
                occupation_transats[p] = r

    # Traitement prioritaire de la liste d'attente
    clients_en_attente = [r for r in resas_du_jour if not r.get("est_place")]
    if clients_en_attente:
        with st.expander(f"⚠️ RÉSÈRVATIONS À PLACER AUJOURD'HUI ({len(clients_en_attente)})", expanded=True):
            for r in clients_en_attente:
                col_c1, col_c2, col_c3 = st.columns([3, 2, 2])
                with col_c1:
                    st.markdown(f"👤 **{r['client']}** — {r['transats']} transat(s) requis (Préf: *{r.get('preference') or 'Aucune'}*)")
                with col_c2:
                    emplacement_choisi = st.text_input("Attribuer Emplacement(s) (Ex: 1-1, 1-2) :", key=f"input_at_{r['id']}")
                with col_c3:
                    if st.button("Assigner & Installer ✅", key=f"btn_at_{r['id']}", type="primary"):
                        if emplacement_choisi.strip():
                            liste_propres = ",".join([p.strip() for p in emplacement_choisi.split(",") if p.strip()])
                            r["emplacement"] = liste_propres
                            r["est_place"] = True
                            sauvegarder_reservation(r)
                            st.session_state.place_selectionnee = liste_propres.split(",")[0]
                            st.rerun()
                        else:
                            st.error("Renseignez un numéro de place.")

    st.write("---")
    
    # Rendu Graphique des 7 lignes x 10 Emplacements Doubles = 140 Transats Max
    for l in range(1, 8):
        st.caption(f"LIGNE DE PLAGE {l}")
        cols_grille = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
        
        # Secteur Ouest : Emplacements 1 à 5
        for g in range(1, 6):
            nom_place = f"{l}-{g}"
            with cols_grille[g - 1]:
                if nom_place in occupation_transats:
                    if st.button(f"🔴\n{occupation_transats[nom_place]['client'][:11]}", key=f"bt_{nom_place}"):
                        st.session_state.place_selectionnee = nom_place
                        st.rerun()
                else:
                    if st.button(f"🟢\n{nom_place}", key=f"bt_{nom_place}"):
                        st.session_state.place_selectionnee = nom_place
                        st.rerun()
                        
        # Couloir d'accès technique / Allée centrale
        with cols_grille[5]:
            st.markdown("<div class='allée-centrale'>ALLÉE</div>", unsafe_allow_html=True)
            
        # Secteur Est : Emplacements 6 à 10
        for g in range(6, 11):
            nom_place = f"{l}-{g}"
            with cols_grille[g]:
                if nom_place in occupation_transats:
                    if st.button(f"🔴\n{occupation_transats[nom_place]['client'][:11]}", key=f"bt_{nom_place}"):
                        st.session_state.place_selectionnee = nom_place
                        st.rerun()
                else:
                    if st.button(f"🟢\n{nom_place}", key=f"bt_{nom_place}"):
                        st.session_state.place_selectionnee = nom_place
                        st.rerun()

    # ==============================================================================
    # PANNEAU DE CONTRÔLE DYNAMIQUE DU TRANSAT SÉLECTIONNÉ
    # ==============================================================================
    if st.session_state.place_selectionnee:
        id_sel = st.session_state.place_selectionnee
        st.write("---")
        st.markdown(f"### 🗂️ Panneau Électronique de l'Emplacement **{id_sel}**")
        
        # SCÉNARIO 1 : L'EMPLACEMENT SÉLECTIONNÉ EST DISPONIBLE
        if id_sel not in occupation_transats:
            st.info(f"L'emplacement {id_sel} ne possède aucune affectation. Enregistrement direct d'un client 'Passage' :")
            with st.form(f"form_passage_{id_sel}"):
                nom = st.text_input("👤 Nom complet du client :")
                nb_t = st.number_input("🪑 Nombre de transats occupés sur ce spot :", min_value=1, max_value=2, value=2)
                h_a = st.text_input("⏰ Heure d'installation :", datetime.now().strftime("%H:%M"))
                h_d = st.text_input("⏳ Heure de libération prévue :", "18:00")
                notes = st.text_area("Notes particulières :")
                
                if st.form_submit_button("🚀 Lancer l'occupation immédiate", type="primary"):
                    if not nom.strip():
                        st.error("Le nom du client de passage est requis.")
                    else:
                        frais = calculer_tarif_plage(h_a, h_d, nb_t)
                        nouvelle_resa = {
                            "client": nom.strip(), "telephone": "Passage", "transats": int(nb_t),
                            "preference": "", "emplacement": id_sel, "est_place": True,
                            "date_resa": str(date_travail), "statut": "Occupé",
                            "heure_arrivee": h_a, "heure_depart": h_d, "montant": frais, "notes": notes.strip(),
                            "transats_payes": False, "conso_ardoise": 0.0, "paye_direct": 0.0, "historique_conso": []
                        }
                        sauvegarder_reservation(nouvelle_resa)
                        st.rerun()
                        
        # SCÉNARIO 2 : L'EMPLACEMENT EST OCCUPÉ — FICHE FINANCIÈRE ET FACTURATION COMPLÈTE
        else:
            client_local = occupation_transats[id_sel]
            
            # Normalisation et sécurité des variables monétaires
            if "transats_payes" not in client_local: client_local["transats_payes"] = False
            if "conso_ardoise" not in client_local: client_local["conso_ardoise"] = 0.0
            if "paye_direct" not in client_local: client_local["paye_direct"] = 0.0
            if "historique_conso" not in client_local: client_local["historique_conso"] = []

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown(f"👤 **Titulaire :** {client_local['client']}")
                st.markdown(f"📍 **Périmètre d'occupation complet :** {client_local['emplacement']}")
                st.markdown(f"⏰ **Heure d'arrivée :** {client_local['heure_arrivee']}")
                
                h_dep_reelle = st.text_input("⏳ Ajuster / Fixer l'heure de départ réelle :", client_local['heure_depart'], key=f"real_dep_{id_sel}")
                frais_transats = calculer_tarif_plage(client_local['heure_arrivee'], h_dep_reelle, client_local['transats'])
                
                if h_dep_reelle != client_local['heure_depart']:
                    client_local['heure_depart'] = h_dep_reelle
                    client_local['montant'] = frais_transats
                    sauvegarder_reservation(client_local)
                
                st.markdown(f"💰 **Tarif Transats Réglementaire : {frais_transats:.2f} €**")
                
                if not client_local["transats_payes"]:
                    st.warning(f"Règlement Transats en attente : {frais_transats:.2f} €")
                    if st.button("💵 Valider Encaissement Transats", key=f"enc_t_{id_sel}"):
                        client_local["transats_payes"] = True
                        client_local["paye_direct"] += frais_transats
                        sauvegarder_reservation(client_local)
                        st.rerun()
                else:
                    st.success("✅ Location des transats encaissée")

            with col_f2:
                st.markdown("🛒 **Ajout de Consommation Bar / Snack**")
                produit = st.selectbox("Sélectionner l'article commandé :", list(TARIFS_CONSO.keys()), key=f"p_{id_sel}")
                prix_u = TARIFS_CONSO[produit]
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("➕ Mettre sur l'Ardoise", key=f"b_ard_{id_sel}"):
                        client_local["conso_ardoise"] += prix_u
                        client_local["historique_conso"].append(f"{produit} (Ardoise — {prix_u:.2f}€)")
                        if produit in st.session_state.stocks:
                            st.session_state.stocks[produit] = max(0, st.session_state.stocks[produit] - 1)
                        sauvegarder_reservation(client_local)
                        st.rerun()
                with col_b2:
                    if st.button("⚡ Encaisser Direct (CB/Espèces)", key=f"b_dir_{id_sel}"):
                        client_local["paye_direct"] += prix_u
                        client_local["historique_conso"].append(f"{produit} (Payé Direct — {prix_u:.2f}€)")
                        if produit in st.session_state.stocks:
                            st.session_state.stocks[produit] = max(0, st.session_state.stocks[produit] - 1)
                        sauvegarder_reservation(client_local)
                        st.rerun()

                if client_local["historique_conso"]:
                    with st.expander("👀 Voir le récapitulatif détaillé des consos"):
                        for item in client_local["historique_conso"]:
                            st.caption(f"• {item}")

            st.write("---")
            reste_transat = 0.0 if client_local["transats_payes"] else frais_transats
            total_solde_du = reste_transat + client_local["conso_ardoise"]
            
            c_m1, c_m2 = st.columns(2)
            c_m1.markdown(f"<div style='background-color: #10b981; color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: bold;'>FLUX ENCAISSÉS SUR CE POSTE : {client_local['paye_direct']:.2f} €</div>", unsafe_allow_html=True)
            c_m2.markdown(f"<div style='background-color: #1e3a8a; color: white; padding: 12px; border-radius: 6px; text-align: center; font-weight: bold; font-size:16px;'>RESTE À PERCEVOIR DU CLIENT : {total_solde_du:.2f} €</div>", unsafe_allow_html=True)

            st.write("")
            col_action1, col_action2 = st.columns(2)
            with col_action1:
                if st.button("🚨 TOUT ENCAISSER & LIBÉRER LE(S) TRANSAT(S)", key=f"lib_{id_sel}", type="primary"):
                    client_local["emplacement"] = ""
                    client_local["est_place"] = False
                    client_local["statut"] = "Clôturé"
                    client_local["montant"] = client_local["paye_direct"] + total_solde_du
                    sauvegarder_reservation(client_local)
                    st.session_state.place_selectionnee = None
                    st.success("Emplacement nettoyé et remis en disponibilité.")
                    st.rerun()
            with col_action2:
                if st.button("Fermer la fiche d'activité", key=f"close_{id_sel}"):
                    st.session_state.place_selectionnee = None
                    st.rerun()

# ==============================================================================
# MODULE 2 : 📝 REGISTRE COMPLET DES RÉSERVATIONS
# ==============================================================================
elif page == "📝 Registre Réservations":
    st.markdown("### 📝 Registre Général des Réservations du Jour")
    
    with st.form("form_nouvelle_resa"):
        st.markdown("##### ➕ Insérer une réservation Planifiée")
        c_r1, c_r2, c_r3 = st.columns([2, 1, 1])
        nom_c = c_r1.text_input("Nom Client :")
        tel_c = c_r2.text_input("Téléphone :")
        nb_tr = c_r3.number_input("Nombre de transats :", min_value=1, max_value=10, value=2)
        
        c_r4, c_r5, c_r6 = st.columns(3)
        h_ar = c_r4.text_input("Heure d'arrivée programmée :", "10:00")
        h_de = c_r5.text_input("Heure de départ programmée :", "18:00")
        pref = c_r6.text_input("Préférence de placement (Ex: Ligne 1, Proche Allée) :")
        
        if st.form_submit_button("Inscrire au registre officiel", type="primary"):
            if nom_c.strip():
                prix_prevu = calculer_tarif_plage(h_ar, h_de, nb_tr)
                nouvelle_resa = {
                    "client": nom_c.strip(), "telephone": tel_c.strip(), "transats": int(nb_tr),
                    "preference": pref.strip(), "emplacement": "", "est_place": False,
                    "date_resa": str(date_travail), "statut": "Confirmé",
                    "heure_arrivee": h_ar, "heure_depart": h_de, "montant": prix_prevu,
                    "transats_payes": False, "conso_ardoise": 0.0, "paye_direct": 0.0, "historique_conso": []
                }
                sauvegarder_reservation(nouvelle_resa)
                st.success(f"Réservation enregistrée pour {nom_c} ({prix_prevu:.2f} € calculés).")
                st.rerun()
            else:
                st.error("Le nom du client est requis.")

    st.write("---")
    st.markdown("##### 📋 Listing opérationnel des mouvements de la journée")
    if not resas_du_jour:
        st.info("Aucune activité enregistrée pour cette date.")
    else:
        for r in resas_du_jour:
            statut_visuel = "📍 Placé en " + r['emplacement'] if r.get('est_place') else "⏳ En attente de placement"
            st.markdown(f"• **{r['client']}** — {r['transats']} Transat(s) — Horaires : {r['heure_arrivee']} à {r['heure_depart']} | **Statut :** `{statut_visuel}`")

# ==============================================================================
# MODULE 3 : 🛶 FLOTTE DE PÉDALOS (MODULE EXPANSION COMPLET AVEC TIMING)
# ==============================================================================
elif page == "🛶 Flotte Pédalos":
    st.markdown("### 🛶 Base Nautique — Supervision de la Flotte de Pédalos")
    
    # Sécurité RAZ journalière de l'état des pédalos
    for k in st.session_state.pedalos:
        if st.session_state.pedalos[k].get("compteur_raz") != str(date_travail):
            st.session_state.pedalos[k] = {"statut": "Disponible", "heure_depart": "", "duree": "1h", "client": "", "compteur_raz": str(date_travail)}

    cols_p = st.columns(5)
    for i in range(1, 6):
        pid = str(i)
        pdata = st.session_state.pedalos[pid]
        with cols_p[i-1]:
            if pdata["statut"] == "Disponible":
                st.markdown(f"<div style='background-color:#d1fae5; padding:10px; border-radius:6px; text-align:center;'><strong>🛶 PÉDALO {pid}</strong><br><span style='color:#065f46;'>Libre</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:#fee2e2; padding:10px; border-radius:6px; text-align:center;'><strong>🛶 PÉDALO {pid}</strong><br><span style='color:#991b1b;'>En mer - {pdata['client'][:10]}</span><br><small>Départ: {pdata['heure_depart']}</small></div>", unsafe_allow_html=True)
            
            if st.button(f"Gérer Pédalo {pid}", key=f"g_ped_{pid}"):
                st.session_state.pedalo_selectionne = pid
                st.rerun()

    if st.session_state.pedalo_selectionne:
        pid = st.session_state.pedalo_selectionne
        pdata = st.session_state.pedalos[pid]
        st.write("---")
        st.markdown(f"#### 🛰️ Contrôle d'Activité Maritime — Pédalo **N° {pid}**")
        
        if pdata["statut"] == "Disponible":
            with st.form(f"f_lancement_pedalo_{pid}"):
                nom_p = st.text_input("Nom du Client / N° Transat :")
                dur = st.selectbox("Durée programmée :", ["1 heure (20€)", "2 heures (35€)", "Demi-heure (15€)"])
                h_dep_p = st.text_input("Heure de mise à l'eau :", datetime.now().strftime("%H:%M"))
                if st.form_submit_button("Lancer l'expédition 🌊", type="primary"):
                    if nom_p.strip():
                        st.session_state.pedalos[pid] = {
                            "statut": "En mer", "heure_depart": h_dep_p, "duree": dur,
                            "client": nom_p.strip(), "compteur_raz": str(date_travail)
                        }
                        st.success(f"Pédalo {pid} marqué en mer.")
                        st.rerun()
                    else:
                        st.error("Nom du client obligatoire pour le registre de sécurité maritime.")
        else:
            st.info(f"📍 **Client à bord :** {pdata['client']} | **Durée :** {pdata['duree']} | **Départ :** {pdata['heure_depart']}")
            px_p = 20.0 if "1 heure" in pdata["duree"] else (35.0 if "2 heures" in pdata["duree"] else 15.0)
            st.markdown(f"💰 **Tarif à percevoir : {px_p:.2f} €**")
            
            if st.button("🏁 Encaisser Retour de Mer & Libérer le matériel", type="primary", key=f"lib_ped_{pid}"):
                st.session_state.pedalos[pid] = {"statut": "Disponible", "heure_depart": "", "duree": "1h", "client": "", "compteur_raz": str(date_travail)}
                st.success(f"Le Pédalo N° {pid} est de retour à la base et disponible.")
                st.session_state.pedalo_selectionne = None
                st.rerun()

# ==============================================================================
# MODULE 4 : 🍹 SUIVI DES STOCKS & CAISSE BUVETTE
# ==============================================================================
elif page == "🍹 Suivi Stocks":
    st.markdown("### 🍹 Inventaire Tournant et Réappro Buvette")
    
    st.info("Les ventes depuis le plan de plage déduisent automatiquement les quantités de cette liste.")
    
    col_st1, col_st2 = st.columns(2)
    
    with col_st1:
        st.markdown("##### 📦 Quantités Restantes au Comptoir")
        for prod, qty in st.session_state.stocks.items():
            c_p1, c_p2, c_p3 = st.columns([3, 1, 2])
            c_p1.write(f"**{prod}** ({TARIFS_CONSO[prod]:.2f} €)")
            
            # Alerte visuelle stock bas
            if qty <= 5:
                c_p2.markdown(f"<span style='color:red; font-weight:bold;'>{qty}</span>", unsafe_allow_html=True)
            else:
                c_p2.write(f"{qty}")
                
            if c_p3.button("➕ 1 Réappro", key=f"add_st_{prod}"):
                st.session_state.stocks[prod] += 1
                st.rerun()

    with col_st2:
        st.markdown("##### 🔧 Ajustement Manuel de l'Inventaire")
        prod_select = st.selectbox("Sélectionner l'article à réajuster :", list(st.session_state.stocks.keys()))
        nouvelle_qte = st.number_input("Définir la nouvelle quantité exacte en stock :", min_value=0, max_value=500, value=int(st.session_state.stocks[prod_select]))
        if st.button("Mettre à jour le stock physique", type="primary"):
            st.session_state.stocks[prod_select] = nouvelle_qte
            st.success(f"Stock de {prod_select} recalibré à {nouvelle_qte} unités.")
            st.rerun()
