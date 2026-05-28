# app.py
import streamlit as st
from supabase import create_client
from datetime import datetime, date
import traceback

# -------------------------
# safe_rerun : fallback pour rerun
# -------------------------
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

# -------------------------
# utilitaires
# -------------------------
def safe_print_exception(prefix="Erreur"):
    st.error(f"{prefix} — voir logs pour la trace complète.")
    print(prefix)
    traceback.print_exc()

def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    try:
        t1 = datetime.strptime(heure_arr, "%H:%M")
        t2 = datetime.strptime(heure_dep, "%H:%M")
        diff = t2 - t1
        minutes = diff.total_seconds() / 60
        if minutes < 0:
            minutes = 0
        heures = minutes / 60.0
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
    except Exception:
        print("Trace calcul_tarif_heures:")
        traceback.print_exc()
        return 15.0 * nb_transats, 0.0, "Tarif Journée (Défaut)"

# -------------------------
# SECRETS SUPABASE
# -------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "SUPABASE_URL_EXEMPLE")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "SUPABASE_KEY_EXEMPLE")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# date du jour (ISO)
aujourd_hui = str(date.today())

# -------------------------
# CONFIG PAGE
# -------------------------
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }
    div[data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; gap: 3px !important; align-items: center !important; padding: 0 !important; }
    .stButton > button { width: 100% !important; height: 55px !important; padding: 0px !important; font-size: 11px !important; line-height: 1.2 !important; font-weight: bold !important; border-radius: 6px !important; }
    .allee-verticale { background-color: #fef08a; color: #854d0e; font-weight: bold; text-align: center; padding: 10px 1px; border-radius: 4px; font-size: 9px; writing-mode: vertical-lr; transform: rotate(180deg); height: 55px; display: flex; align-items: center; justify-content: center; }
    .total-display { background-color: #1e3a8a; color: white; padding: 12px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin-top: 10px; margin-bottom: 10px; }
    .paye-direct-display { background-color: #10b981; color: white; padding: 10px; border-radius: 8px; text-align: center; font-size: 14px; font-weight: bold; margin-top: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# AUTHENTIFICATION SIMPLE
# -------------------------
if "autorise" not in st.session_state:
    st.session_state.autorise = False
mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e;'>🏖️ Chez Alex - Équipe</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        mdp = st.text_input("Mot de passe :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary"):
            if mdp == mdp_secret:
                st.session_state.autorise = True
                safe_rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    st.stop()

# -------------------------
# INITIALISATION session_state
# -------------------------
if "plage" not in st.session_state:
    st.session_state.plage = {}
if not st.session_state.plage:
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            st.session_state.plage[id_c] = {
                "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
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

if "ca_jour" not in st.session_state:
    st.session_state.ca_jour = 0.0
if "stocks" not in st.session_state:
    st.session_state.stocks = {
        "Coca-Cola": 150, "Orangina": 40, "Menthe & Citrons (Mojito)": 30, "Glaces Artisanales": 60
    }
if "notes" not in st.session_state:
    st.session_state.notes = []
if "groupe_selectionne" not in st.session_state:
    st.session_state.groupe_selectionne = None
if "reservations" not in st.session_state:
    st.session_state.reservations = {}

# -------------------------
# CHARGEMENT SUPABASE (lecture) paramétrable par date
# -------------------------
def charger_donnees_depuis_supabase(date_iso=None):
    try:
        target_date = date_iso or aujourd_hui
        rep = supabase.table("transats").select("*").eq("date", target_date).execute()
        rows = rep.data or []
        for ligne in rows:
            id_c = ligne.get("numero_transat")
            if not id_c:
                continue
            if id_c not in st.session_state.plage:
                continue
            st.session_state.plage[id_c]["statut"] = ligne.get("statut_paiement", "Occupé")
            st.session_state.plage[id_c]["client"] = ligne.get("nom_client", "")
            try:
                st.session_state.plage[id_c]["prix_transats_encaisse"] = float(ligne.get("prix", 0.0))
            except:
                st.session_state.plage[id_c]["prix_transats_encaisse"] = 0.0
    except Exception:
        safe_print_exception("Erreur chargement transats depuis Supabase")

# Charger une fois par session pour aujourd'hui si besoin
if "donnees_chargees" not in st.session_state:
    charger_donnees_depuis_supabase()
    st.session_state.donnees_chargees = True

# -------------------------
# SIDEBAR NAVIGATION
# -------------------------
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
        safe_rerun()

# -------------------------
# MODULES PRINCIPAUX
# -------------------------
if page == "🏖️ Plan de la plage":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)

    # Sélecteur de date pour le plan (lié aux réservations)
    date_plan = st.date_input("Choisir la date du plan", value=datetime.now().date(), key="date_plan")
    date_plan_iso = date_plan.strftime("%Y-%m-%d")
    date_plan_clef = date_plan.strftime("%d/%m/%Y")
    # NOTE: ne pas réassigner st.session_state["date_plan"] ici (évite StreamlitAPIException)

    # Charger les transats depuis Supabase pour la date sélectionnée
    charger_donnees_depuis_supabase(date_iso=date_plan_iso)

    # Récupérer les réservations locales pour la date sélectionnée
    resas_du_jour = st.session_state.reservations.get(date_plan_clef, [])

    # Appliquer les réservations assignées sur la grille (si la place est libre)
    for resa in resas_du_jour:
        assigned = resa.get("assigned_place")
        if assigned and assigned in st.session_state.plage:
            if st.session_state.plage[assigned].get("statut","Libre") == "Libre":
                st.session_state.plage[assigned].update({
                    "statut": "Occupé",
                    "client": resa.get("client",""),
                    "nb_transats": resa.get("transats",2),
                    "heure_arrivee": "09:00",
                    "transats_payes": False,
                    "prix_transats_encaisse": 0.0,
                    "conso_ardoise": 0.0,
                    "historique_conso": [],
                    "paye_direct": 0.0,
                    "historique_paye_direct": []
                })

    # affichage grille
    for l in range(1, 8):
        st.caption(f"Ligne {l}")
        cols = st.columns([1,1,1,1,1,0.4,1,1,1,1,1])
        for g in range(1, 6):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut","Libre") == "Libre" else f"🔴\n{info.get('client','Occupé')}"
            if cols[g-1].button(label, key=f"btn_place_{id_c}"):
                st.session_state.groupe_selectionne = id_c
                safe_rerun()
        with cols[5]:
            st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)
        for g in range(6, 11):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut","Libre") == "Libre" else f"🔴\n{info.get('client','Occupé')}"
            if cols[g].button(label, key=f"btn_place_{id_c}_r"):
                st.session_state.groupe_selectionne = id_c
                safe_rerun()

    # ---------------------------
    # Gestion de la place sélectionnée en modal (superposition)
    # ---------------------------
    if st.session_state.groupe_selectionne:
        id_sel = st.session_state.groupe_selectionne
        info = st.session_state.plage.get(id_sel, {})
        if "historique_conso" not in info: info["historique_conso"] = []
        if "historique_paye_direct" not in info: info["historique_paye_direct"] = []
        if "paye_direct" not in info: info["paye_direct"] = 0.0
        if "conso_ardoise" not in info: info["conso_ardoise"] = 0.0

        with st.modal(f"Gérer {id_sel}", clear_on_close=False):
            info_local = st.session_state.plage[id_sel]
            num_l, num_g = id_sel.replace("L","").split("-G")
            st.markdown(f"### Emplacement **{num_l}-{num_g}**")
            st.write("")
            if info_local.get("statut","Libre") == "Libre":
                nom = st.text_input("👤 Nom du client :", key=f"nom_client_{id_sel}")
                nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=info_local.get("nb_transats",2), key=f"nbt_{id_sel}")
                h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"), key=f"ha_{id_sel}")
                if st.button("✅ Installer le client", key=f"installer_{id_sel}", type="primary"):
                    if not nom:
                        st.error("Nom obligatoire.")
                    else:
                        st.session_state.plage[id_sel].update({
                            "statut":"Occupé","client":nom,"nb_transats":nb_t,"heure_arrivee":h_a,
                            "transats_payes":False,"prix_transats_encaisse":0.0,"conso_ardoise":0.0,
                            "historique_conso":[],"paye_direct":0.0,"historique_paye_direct":[]
                        })
                        date_for_insert = date_plan.isoformat()
                        try:
                            supabase.table("transats").insert({
                                "date": date_for_insert,
                                "numero_transat": id_sel,
                                "nom_client": nom,
                                "periode": "Journée",
                                "prix": 0.0,
                                "statut_paiement": "Occupé"
                            }).execute()
                        except Exception:
                            pass
                        st.success("Client installé.")
                        safe_rerun()
            else:
                st.markdown(f"**Client :** {info_local.get('client','-')}  |  **Transats :** {info_local.get('nb_transats',2)}  |  **Arrivée :** {info_local.get('heure_arrivee','-')}")
                h_actuelle = datetime.now().strftime("%H:%M")
                h_dep = st.text_input("⏳ Heure de départ / calcul :", h_actuelle, key=f"hd_{id_sel}")
                frais_transats, heures_passees, libelle_tarif = calculer_tarif_heures(info_local.get("heure_arrivee","00:00"), h_dep, info_local.get("nb_transats",2))
                st.markdown(f"⏱️ *Temps : {heures_passees:.2f}h* — **{libelle_tarif}**")
                st.write("---")
                st.write("💰 **Règlement des Transats :**")
                if not info_local.get("transats_payes", False):
                    st.warning(f"Montant dû : {frais_transats:.2f} €")
                    if st.button("💵 Encaisser les transats DIRECT (Sur le transat)", key=f"encaisser_transat_{id_sel}"):
                        st.session_state.ca_jour = st.session_state.get("ca_jour",0.0) + frais_transats
                        st.session_state.plage[id_sel]["transats_payes"] = True
                        st.session_state.plage[id_sel]["prix_transats_encaisse"] = frais_transats
                        try:
                            supabase.table("transats").update({
                                "prix": frais_transats,
                                "statut_paiement": "Payé"
                            }).eq("date", date_plan.isoformat()).eq("numero_transat", id_sel).execute()
                        except Exception:
                            pass
                        st.success("Transats encaissés.")
                        safe_rerun()
                else:
                    st.success(f"✅ Transats réglés ({info_local.get('prix_transats_encaisse',0.0):.2f} €)")
                st.write("---")
                st.write("🛒 **Ajouter une Consommation :**")
                produit_choisi = st.selectbox("Choisir l'article :", list(TARIFS_CONSO.keys()), key=f"sel_prod_{id_sel}")
                prix_unitaire = TARIFS_CONSO[produit_choisi]
                st.info(f"Prix unitaire : {prix_unitaire:.2f} €")
                col_btn_ard, col_btn_dir = st.columns(2)
                with col_btn_ard:
                    if st.button("➕ Ajouter à l'Ardoise", key=f"btn_ard_{id_sel}"):
                        try:
                            st.session_state.plage[id_sel]["conso_ardoise"] = st.session_state.plage[id_sel].get("conso_ardoise",0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                            st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi,0) - 1
                            nouvelle_conso = {
                                "article": produit_choisi,
                                "quantite": 1,
                                "prix_total": prix_unitaire,
                                "numero_transat_associe": id_sel,
                                "date": date_plan.isoformat()
                            }
                            supabase.table("consommations").insert(nouvelle_conso).execute()
                        except Exception:
                            pass
                        safe_rerun()
                with col_btn_dir:
                    if st.button("⚡ Encaisser Direct", key=f"btn_dir_{id_sel}"):
                        try:
                            st.session_state.ca_jour = st.session_state.get("ca_jour",0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["paye_direct"] = st.session_state.plage[id_sel].get("paye_direct",0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                            st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi,0) - 1
                            nouvelle_conso = {
                                "article": produit_choisi,
                                "quantite": 1,
                                "prix_total": prix_unitaire,
                                "date": date_plan.isoformat()
                            }
                            supabase.table("consommations").insert(nouvelle_conso).execute()
                        except Exception:
                            pass
                        safe_rerun()
                if info_local.get("historique_conso") or info_local.get("historique_paye_direct"):
                    with st.expander("👀 Voir le détail des consos"):
                        if info_local.get("historique_conso"):
                            st.write("**Sur l'Ardoise :**")
                            for c in info_local["historique_conso"]:
                                st.text(f" ⏳ {c}")
                        if info_local.get("historique_paye_direct"):
                            st.write("**Déjà payé en direct :**")
                            for c in info_local["historique_paye_direct"]:
                                st.text(f" ✅ {c}")
                st.write("---")
                transats_dus = 0.0 if info_local.get("transats_payes", False) else frais_transats
                total_du_final = transats_dus + info_local.get("conso_ardoise", 0.0)
                st.markdown(f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ EN DIRECT : {info_local.get('paye_direct', 0.0) + info_local.get('prix_transats_encaisse', 0.0):.2f} €</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='total-display'>RESTE À PAYER AU DÉPART : {total_du_final:.2f} €</div>", unsafe_allow_html=True)
                col_f1, col_f2 = st.columns(2)
                if col_f1.button("💵 ENCAISSER RESTE & LIBÉRER", key=f"liberer_{id_sel}"):
                    try:
                        st.session_state.ca_jour = st.session_state.get("ca_jour",0.0) + total_du_final
                        supabase.table("transats").update({
                            "prix": info_local.get('prix_transats_encaisse', 0.0) + transats_dus,
                            "statut_paiement": "Libre"
                        }).eq("date", date_plan.isoformat()).eq("numero_transat", id_sel).execute()
                    except Exception:
                        pass
                    st.session_state.plage[id_sel] = {
                        "statut":"Libre","client":"","heure_arrivee":"","nb_transats":2,
                        "transats_payes":False,"prix_transats_encaisse":0.0,"conso_ardoise":0.0,
                        "historique_conso":[],"paye_direct":0.0,"historique_paye_direct":[]
                    }
                    st.session_state.groupe_selectionne = None
                    safe_rerun()
                if col_f2.button("Fermer", key=f"fermer_{id_sel}"):
                    st.session_state.groupe_selectionne = None
                    safe_rerun()

# ---------------------------
# Réservations (nouvelle version avec bouton plan modal)
# ---------------------------
elif page == "📅 Réservations":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📅 GESTION DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
    st.write("---")
    col_form, col_list = st.columns([2,3])

    # Formulaire de création (préférence, téléphone, enfants)
    with col_form:
        date_resa = st.date_input("Date de la réservation", value=datetime.now().date(), key="resa_date")
        preference = st.selectbox("Préférence emplacement", ["1er rang", "Allée", "Corde"], key="resa_preference")
        client_resa = st.text_input("Nom du client", key="resa_client")
        tel_resa = st.text_input("Téléphone", key="resa_tel")
        enfants = st.checkbox("Y a-t-il des enfants ?", key="resa_enfants")
        transats_resa = st.number_input("Nombre de transats", min_value=1, max_value=4, value=2, key="resa_transats")
        periode_resa = st.selectbox("Période", ["Matin","Journée","Après-midi"], key="resa_periode")
        if st.button("Enregistrer la réservation"):
            date_clef = date_resa.strftime("%d/%m/%Y")
            if date_clef not in st.session_state.reservations:
                st.session_state.reservations[date_clef] = []
            nouvelle = {
                "preference": preference,
                "client": client_resa,
                "telephone": tel_resa,
                "enfants": bool(enfants),
                "transats": transats_resa,
                "periode": periode_resa,
                "assigned_place": None
            }
            st.session_state.reservations[date_clef].append(nouvelle)
            try:
                supabase.table("reservations").insert({
                    "date": date_resa.isoformat(),
                    "preference": preference,
                    "nom_client": client_resa,
                    "telephone": tel_resa,
                    "enfants": bool(enfants),
                    "transats": transats_resa,
                    "periode": periode_resa,
                    "assigned_place": None
                }).execute()
            except Exception:
                pass
            st.success("Réservation ajoutée.")
            safe_rerun()

    # Colonne de droite : bouton pour ouvrir le plan modal + liste
    with col_list:
        st.markdown("### 📋 Réservations enregistrées")
        date_affiche = st.date_input("Date affichée", value=datetime.now().date(), key="resa_date_affiche")
        date_affiche_clef = date_affiche.strftime("%d/%m/%Y")

        # Bouton pour ouvrir le plan des réservations en modal
        if st.button("Afficher le plan des emplacements", key="btn_afficher_plan"):
            with st.modal("Plan des emplacements (cliquer sur une place)"):
                st.markdown("### Plan interactif")
                cols_per_line = [1,1,1,1,1,0.4,1,1,1,1,1]
                for l in range(1, 8):
                    row_cols = st.columns(cols_per_line)
                    for g in range(1, 6):
                        id_c = f"L{l}-G{g}"
                        assigned = any(r.get("assigned_place") == id_c for r in st.session_state.reservations.get(date_affiche_clef, []))
                        label = f"🟡\n{l}-{g}" if assigned else f"⚪\n{l}-{g}"
                        if row_cols[g-1].button(label, key=f"modal_place_{id_c}"):
                            st.markdown(f"#### Place {id_c} — Réservations pour {date_affiche_clef}")
                            listes = st.session_state.reservations.get(date_affiche_clef, [])
                            candidats = []
                            for idx, rr in enumerate(listes):
                                if rr.get("assigned_place") in (None, id_c):
                                    candidats.append((idx, rr))
                            if not candidats:
                                st.info("Aucune réservation correspondante pour cette place.")
                            else:
                                for idx, rr in candidats:
                                    st.write(f"- **{rr.get('client','-')}** — {rr.get('transats')} transats — Préf: {rr.get('preference')} — Tel: {rr.get('telephone','-')} — Enfants: {'Oui' if rr.get('enfants') else 'Non'} — Emplacement: {rr.get('assigned_place') or 'Non assigné'}")
                                    col1, col2 = st.columns([1,1])
                                    if col1.button("Assigner ici", key=f"assign_here_{id_c}_{idx}"):
                                        st.session_state.reservations[date_affiche_clef][idx]["assigned_place"] = id_c
                                        try:
                                            rep = supabase.table("reservations").select("*").eq("date", date_affiche.isoformat()).eq("nom_client", rr.get("client")).execute()
                                            rows = rep.data or []
                                            if rows:
                                                supabase.table("reservations").update({"assigned_place": id_c}).eq("id", rows[0].get("id")).execute()
                                        except Exception:
                                            pass
                                        st.success(f"{rr.get('client')} assigné(e) à {id_c}.")
                                        safe_rerun()
                                    if col2.button("Voir détails", key=f"voir_det_{id_c}_{idx}"):
                                        st.write(rr)
                    with row_cols[5]:
                        st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)
                    for g in range(6, 11):
                        id_c = f"L{l}-G{g}"
                        assigned = any(r.get("assigned_place") == id_c for r in st.session_state.reservations.get(date_affiche_clef, []))
                        label = f"🟡\n{l}-{g}" if assigned else f"⚪\n{l}-{g}"
                        if row_cols[g].button(label, key=f"modal_place_{id_c}_r"):
                            st.markdown(f"#### Place {id_c} — Réservations pour {date_affiche_clef}")
                            listes = st.session_state.reservations.get(date_affiche_clef, [])
                            candidats = []
                            for idx, rr in enumerate(listes):
                                if rr.get("assigned_place") in (None, id_c):
                                    candidats.append((idx, rr))
                            if not candidats:
                                st.info("Aucune réservation correspondante pour cette place.")
                            else:
                                for idx, rr in candidats:
                                    st.write(f"- **{rr.get('client','-')}** — {rr.get('transats')} transats — Préf: {rr.get('preference')} — Tel: {rr.get('telephone','-')}")
                                    col1, col2 = st.columns([1,1])
                                    if col1.button("Assigner ici", key=f"assign_here_{id_c}_{idx}_r"):
                                        st.session_state.reservations[date_affiche_clef][idx]["assigned_place"] = id_c
                                        try:
                                            rep = supabase.table("reservations").select("*").eq("date", date_affiche.isoformat()).eq("nom_client", rr.get("client")).execute()
                                            rows = rep.data or []
                                            if rows:
                                                supabase.table("reservations").update({"assigned_place": id_c}).eq("id", rows[0].get("id")).execute()
                                        except Exception:
                                            pass
                                        st.success(f"{rr.get('client')} assigné(e) à {id_c}.")
                                        safe_rerun()
                                    if col2.button("Voir détails", key=f"voir_det_{id_c}_{idx}_r"):
                                        st.write(rr)

        st.write("---")
        st.markdown(f"### Réservations pour {date_affiche_clef}")
        listes = st.session_state.reservations.get(date_affiche_clef, [])
        if not listes:
            st.info("Aucune réservation pour cette date.")
        else:
            for i, r in enumerate(listes):
                assigned = r.get("assigned_place")
                st.write(f"**{r.get('client','-')}** — {r.get('transats')} transats — {r.get('periode')} — Préf : {r.get('preference')} — Tel: {r.get('telephone','-')} — Enfants: {'Oui' if r.get('enfants') else 'Non'} — Emplacement: {assigned or 'Non assigné'}")
                col_a, col_b, col_c = st.columns([1,1,1])
                if col_a.button("Annuler", key=f"annuler_resa_{date_affiche_clef}_{i}"):
                    resa = st.session_state.reservations[date_affiche_clef].pop(i)
                    try:
                        rep = supabase.table("reservations").select("*").eq("date", date_affiche.isoformat()).eq("nom_client", resa["client"]).execute()
                        rows = rep.data or []
                        for row in rows:
                            supabase.table("reservations").delete().eq("id", row.get("id")).execute()
                    except Exception:
                        pass
                    st.success("Réservation annulée.")
                    safe_rerun()
                if col_b.button("Modifier préférence / infos", key=f"modif_resa_{date_affiche_clef}_{i}"):
                    new_pref = st.selectbox("Nouvelle préférence", ["1er rang","Allée","Corde"], key=f"mod_pref_{date_affiche_clef}_{i}")
                    new_tel = st.text_input("Téléphone", value=r.get("telephone",""), key=f"mod_tel_{date_affiche_clef}_{i}")
                    new_enf = st.checkbox("Enfants ?", value=r.get("enfants", False), key=f"mod_enf_{date_affiche_clef}_{i}")
                    new_trans = st.number_input("Nombre de transats", min_value=1, max_value=4, value=r.get("transats",2), key=f"mod_trans_{date_affiche_clef}_{i}")
                    if st.button("Valider modification", key=f"valider_modif_{date_affiche_clef}_{i}"):
                        st.session_state.reservations[date_affiche_clef][i].update({
                            "preference": new_pref, "telephone": new_tel, "enfants": bool(new_enf), "transats": new_trans
                        })
                        try:
                            rep = supabase.table("reservations").select("*").eq("date", date_affiche.isoformat()).eq("nom_client", r.get("client")).execute()
                            rows = rep.data or []
                            if rows:
                                supabase.table("reservations").update({
                                    "preference": new_pref, "telephone": new_tel, "enfants": bool(new_enf), "transats": new_trans
                                }).eq("id", rows[0].get("id")).execute()
                        except Exception:
                            pass
                        st.success("Modification enregistrée.")
                        safe_rerun()
                if col_c.button("Placer sur le plan", key=f"placer_resa_{date_affiche_clef}_{i}"):
                    with st.modal(f"Placer {r.get('client')} sur le plan"):
                        st.markdown(f"### Placer {r.get('client')}")
                        pref = r.get("preference")
                        candidates = []
                        if pref == "1er rang":
                            for g in range(1, 11):
                                candidates.append(f"L1-G{g}")
                        elif pref == "Allée":
                            for l in range(1,8):
                                candidates.append(f"L{l}-G6")
                        else:
                            for g in range(1, 11):
                                candidates.append(f"L7-G{g}")
                        free_candidates = [c for c in candidates if st.session_state.plage.get(c, {}).get("statut","Libre") == "Libre"]
                        if free_candidates:
                            sel_place = st.selectbox("Choisir un emplacement proposé", free_candidates, key=f"sel_place_pref_{date_affiche_clef}_{i}")
                        else:
                            all_free = [k for k,v in st.session_state.plage.items() if v.get("statut","Libre") == "Libre"]
                            if not all_free:
                                st.info("Aucune place libre.")
                                sel_place = None
                            else:
                                sel_place = st.selectbox("Choisir une place libre", all_free, key=f"sel_place_any_{date_affiche_clef}_{i}")
                        if st.button("Valider placement", key=f"valider_placement_{date_affiche_clef}_{i}"):
                            if sel_place:
                                st.session_state.reservations[date_affiche_clef][i]["assigned_place"] = sel_place
                                plan_date = st.session_state.get("date_plan", date_plan).strftime("%d/%m/%Y") if isinstance(st.session_state.get("date_plan", date_plan), date) else date_plan.strftime("%d/%m/%Y")
                                if date_affiche_clef == plan_date:
                                    st.session_state.plage[sel_place].update({
                                        "statut":"Occupé","client": r.get("client",""), "nb_transats": r.get("transats",2),
                                        "heure_arrivee":"09:00","transats_payes":False,"prix_transats_encaisse":0.0,
                                        "conso_ardoise":0.0,"historique_conso":[],"paye_direct":0.0,"historique_paye_direct":[]
                                    })
                                try:
                                    rep = supabase.table("reservations").select("*").eq("date", date_affiche.isoformat()).eq("nom_client", r.get("client")).execute()
                                    rows = rep.data or []
                                    if rows:
                                        supabase.table("reservations").update({"assigned_place": sel_place}).eq("id", rows[0].get("id")).execute()
                                    rep_t = supabase.table("transats").select("*").eq("date", date_affiche.isoformat()).eq("numero_transat", sel_place).execute()
                                    rows_t = rep_t.data or []
                                    if rows_t:
                                        supabase.table("transats").update({
                                            "nom_client": r.get("client",""),
                                            "periode": r.get("periode","Journée"),
                                            "prix": 0.0,
                                            "statut_paiement": "Occupé"
                                        }).eq("id", rows_t[0].get("id")).execute()
                                    else:
                                        supabase.table("transats").insert({
                                            "date": date_affiche.isoformat(),
                                            "numero_transat": sel_place,
                                            "nom_client": r.get("client",""),
                                            "periode": r.get("periode","Journée"),
                                            "prix": 0.0,
                                            "statut_paiement": "Occupé"
                                        }).execute()
                                except Exception:
                                    pass
                                st.success("Placement effectué.")
                                safe_rerun()

# ---------------------------
# Chiffre d'Affaires
# ---------------------------
elif page == "📊 Chiffre d'Affaires":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📊 CHIFFRE D'AFFAIRES</h3>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([2,1])
    with col1:
        st.metric("CA (jour)", f"{st.session_state.get('ca_jour',0.0):.2f} €")
        st.write("Détail des encaissements par emplacement :")
        for id_c, info in st.session_state.plage.items():
            total_encaisse = info.get("paye_direct",0.0) + info.get("prix_transats_encaisse",0.0)
            if total_encaisse > 0:
                st.write(f"- {id_c} : {info.get('client','-')} — {total_encaisse:.2f} €")
    with col2:
        if st.button("Sauvegarder CA du jour dans Supabase"):
            try:
                supabase.table("ca_journalier").insert({
                    "date": aujourd_hui,
                    "ca_total": float(st.session_state.get("ca_jour",0.0))
                }).execute()
                st.success("CA sauvegardé.")
            except Exception:
                st.error("Erreur sauvegarde CA (vérifie la table ca_journalier).")
        if st.button("Réinitialiser CA du jour (local)"):
            st.session_state.ca_jour = 0.0
            safe_rerun()
    st.write("---")
    st.markdown("### Historique (dernières entrées Supabase)")
    try:
        rep = supabase.table("ca_journalier").select("*").order("date", desc=True).limit(10).execute()
        rows = rep.data or []
        if rows:
            for r in rows:
                st.write(f"- {r.get('date')} : {r.get('ca_total',0.0):.2f} €")
        else:
            st.info("Aucune donnée CA en base.")
    except Exception:
        st.info("Impossible de lire l'historique CA depuis Supabase.")

# ---------------------------
# Récap Journalier
# ---------------------------
elif page == "📊 Récap Journalier":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📊 RÉCAP JOURNALIER</h3>", unsafe_allow_html=True)
    st.write("---")
    date_sel = st.date_input("Choisir une date", value=datetime.now().date(), key="recap_date")
    date_clef = date_sel.strftime("%Y-%m-%d")
    st.markdown("#### Transats enregistrés (Supabase)")
    try:
        rep_t = supabase.table("transats").select("*").eq("date", date_clef).execute()
        rows_t = rep_t.data or []
        if rows_t:
            for r in rows_t:
                st.write(f"- {r.get('numero_transat')} | {r.get('nom_client','-')} | {r.get('statut_paiement','-')} | {r.get('prix',0.0):.2f} €")
        else:
            st.info("Aucun transat enregistré pour cette date en base.")
    except Exception:
        st.info("Impossible de lire les transats depuis Supabase.")
    st.write("---")
    st.markdown("#### Consommations enregistrées (Supabase)")
    try:
        rep_c = supabase.table("consommations").select("*").eq("date", date_clef).execute()
        rows_c = rep_c.data or []
        if rows_c:
            for c in rows_c:
                st.write(f"- {c.get('article')} | qté: {c.get('quantite',1)} | {c.get('prix_total',0.0):.2f} € | transat: {c.get('numero_transat_associe','-')}")
        else:
            st.info("Aucune consommation enregistrée pour cette date en base.")
    except Exception:
        st.info("Impossible de lire les consommations depuis Supabase.")

# ---------------------------
# Pédalos (séparateur entre chaque)
# ---------------------------
elif page == "🛶 Pédalos":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>🛶 GESTION DE LA FLOTTE DE PÉDALOS</h3>", unsafe_allow_html=True)
    st.write("---")
    for idx, (p_id, p_info) in enumerate(st.session_state.pedalos.items()):
        with st.container():
            col_p1, col_p2, col_p3 = st.columns([2,4,3])
            with col_p1:
                if p_info["statut"] == "Disponible":
                    st.markdown(f"### 🔵 {p_id}")
                    st.success("Disponible")
                else:
                    st.markdown(f"### 🛶 {p_id}")
                    st.error("En Mer")
            with col_p2:
                if p_info["statut"] == "Disponible":
                    nom_p = st.text_input("Nom du client :", key=f"nom_{p_id}", placeholder="Ex: Lucas")
                    duree_p = st.radio("Durée demandée :", ["30 min (15€)","1h (20€)"], key=f"dur_{p_id}", horizontal=True)
                    h_dep_p = st.text_input("Heure de départ :", datetime.now().strftime("%H:%M"), key=f"hdep_{p_id}")
                else:
                    st.markdown(f"👤 **Client :** {p_info['client']}")
                    st.markdown(f"⏰ **Départ :** {p_info['heure_depart']} | **Forfait :** {p_info['duree_prevue']}")
                    st.markdown(f"💰 **Montant à régler :** {p_info['total_du']:.2f} €")
            with col_p3:
                st.write("")
                if p_info["statut"] == "Disponible":
                    if st.button("🚀 Mettre à l'eau", key=f"btn_l_{p_id}", use_container_width=True):
                        if st.session_state.get(f"nom_{p_id}", ""):
                            nom_val = st.session_state.get(f"nom_{p_id}")
                            prix_p = 15.0 if "30 min" in st.session_state.get(f"dur_{p_id}", "") else 20.0
                            st.session_state.pedalos[p_id].update({
                                "statut":"En Mer","client":nom_val,"heure_depart":h_dep_p,"duree_prevue":st.session_state.get(f"dur_{p_id}","1h"),"total_du":prix_p
                            })
                            safe_rerun()
                        else:
                            st.error("Entrez un nom")
                else:
                    if st.button("💵 Retour & Encaisser", key=f"btn_r_{p_id}", use_container_width=True):
                        st.session_state.ca_jour += p_info["total_du"]
                        st.session_state.pedalos[p_id].update({
                            "statut":"Disponible","client":"","heure_depart":"","duree_prevue":"1h","total_du":0.0
                        })
                        safe_rerun()
        if idx < len(st.session_state.pedalos) - 1:
            st.markdown("---")

# ---------------------------
# Notes (To-Do)
# ---------------------------
elif page == "📝 Notes (To-Do List)":
    st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
    col_note, col_btn = st.columns([4,1])
    nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Nettoyer la ligne 3")
    if col_btn.button("Ajouter"):
        if nouvelle_note:
            st.session_state.notes.append(nouvelle_note)
            safe_rerun()
    st.write("---")
    notes_a_supprimer = []
    for i, note in enumerate(st.session_state.notes):
        if st.checkbox(note, key=f"note_{i}"):
            notes_a_supprimer.append(i)
    if notes_a_supprimer:
        for i in reversed(notes_a_supprimer):
            st.session_state.notes.pop(i)
        safe_rerun()

# ---------------------------
# Stocks & Frigos (avec -1 et saisie précise)
# ---------------------------
elif page == "📦 Stocks & Frigos":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📦 GESTION DES STOCKS & FRIGOS</h3>", unsafe_allow_html=True)
    st.write("---")
    st.info("💡 Cet onglet sert uniquement à enregistrer les livraisons (Réassort). Les stocks diminuent automatiquement à chaque vente sur le plan de la plage.")
    col_h1, col_h2, col_h3 = st.columns([3,1.5,2])
    with col_h1: st.markdown("**Produit**")
    with col_h2: st.markdown("**Quantité en réserve**")
    with col_h3: st.markdown("**Actions**")
    st.write("---")
    for produit in TARIFS_CONSO.keys():
        if produit not in st.session_state.stocks:
            st.session_state.stocks[produit] = 0
        quantite_actuelle = st.session_state.stocks[produit]
        col_nom, col_qte, col_actions = st.columns([3,1.5,2])
        with col_nom:
            st.write(f"🍹 {produit}")
        with col_qte:
            if quantite_actuelle <= 5:
                if st.button(f"{quantite_actuelle} ⚠️ (Bas)", key=f"qte_btn_{produit}"):
                    with st.modal(f"Modifier stock {produit}"):
                        st.markdown(f"### Modifier le stock de {produit}")
                        new_q = st.number_input("Nouvelle quantité", min_value=0, value=quantite_actuelle, key=f"new_q_{produit}")
                        if st.button("Valider", key=f"valider_q_{produit}"):
                            st.session_state.stocks[produit] = int(new_q)
                            safe_rerun()
            else:
                if st.button(str(quantite_actuelle), key=f"qte_btn_{produit}"):
                    with st.modal(f"Modifier stock {produit}"):
                        st.markdown(f"### Modifier le stock de {produit}")
                        new_q = st.number_input("Nouvelle quantité", min_value=0, value=quantite_actuelle, key=f"new_q_{produit}")
                        if st.button("Valider", key=f"valider_q_{produit}"):
                            st.session_state.stocks[produit] = int(new_q)
                            safe_rerun()
        with col_actions:
            btn_col1, btn_col2, btn_col3 = st.columns([1,1,1])
            if btn_col1.button("➕ 1", key=f"plus1_{produit}"):
                st.session_state.stocks[produit] += 1
                safe_rerun()
            if btn_col2.button("➕ 10", key=f"plus10_{produit}"):
                st.session_state.stocks[produit] += 10
                safe_rerun()
            if btn_col3.button("➖ 1", key=f"minus1_{produit}"):
                st.session_state.stocks[produit] = max(0, st.session_state.stocks[produit] - 1)
                safe_rerun()

# ---------------------------
# Default
# ---------------------------
else:
    st.write("Page en construction ou non implémentée.")
