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
    .pedalo-sep { border-top: 2px solid rgba(0,0,0,0.06); margin: 8px 0; }
    .small-number-btn { background: transparent; border: none; color: #0b6fe0; font-weight: 700; cursor: pointer; }
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
if "resa_plan_place_selected" not in st.session_state:
    st.session_state.resa_plan_place_selected = None

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
# Helper : format date keys
# -------------------------
def date_to_key(d: date):
    return d.strftime("%d/%m/%Y")

# -------------------------
# PLAN DE LA PLAGE
# -------------------------
if page == "🏖️ Plan de la plage":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)

    # Choix de la date du plan (connectée aux réservations)
    date_plan = st.date_input("Choisir la date du plan", value=datetime.now().date(), key="date_plan")
    date_plan_iso = date_plan.strftime("%Y-%m-%d")
    date_plan_clef = date_to_key(date_plan)

    # Charger données supabase pour la date sélectionnée
    charger_donnees_depuis_supabase(date_iso=date_plan_iso)

    # Appliquer les réservations assignées pour cette date (liaison réservation -> plan)
    resas_du_jour = st.session_state.reservations.get(date_plan_clef, [])
    for resa in resas_du_jour:
        assigned = resa.get("assigned_place")
        assigned_date = resa.get("assigned_date")
        # si la réservation a été assignée pour cette date, on l'affiche sur le plan
        if assigned and assigned_date == date_plan_clef:
            if assigned in st.session_state.plage:
                # n'écrase pas si déjà occupé par autre chose (priorité : Supabase / installation)
                if st.session_state.plage[assigned].get("statut", "Libre") == "Libre":
                    st.session_state.plage[assigned].update({
                        "statut": "Occupé",
                        "client": resa.get("client", ""),
                        "nb_transats": resa.get("transats", 2),
                        "heure_arrivee": resa.get("heure_arrivee", "09:00"),
                        "transats_payes": False,
                        "prix_transats_encaisse": 0.0,
                        "conso_ardoise": 0.0,
                        "historique_conso": [],
                        "paye_direct": 0.0,
                        "historique_paye_direct": []
                    })

    # Rendu du plan : grille de lignes et colonnes
    for l in range(1, 8):
        st.caption(f"Ligne {l}")
        cols = st.columns([1,1,1,1,1,0.4,1,1,1,1,1])
        # gauche
        for g in range(1, 6):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut","Libre") == "Libre" else f"🔴\n{info.get('client','Occupé')}"
            if cols[g-1].button(label, key=f"btn_place_{id_c}"):
                st.session_state.groupe_selectionne = id_c
                safe_rerun()
        # allée verticale
        with cols[5]:
            st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)
        # droite
        for g in range(6, 11):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut","Libre") == "Libre" else f"🔴\n{info.get('client','Occupé')}"
            if cols[g].button(label, key=f"btn_place_{id_c}_r"):
                st.session_state.groupe_selectionne = id_c
                safe_rerun()

    # Gestion de la place sélectionnée via modal (superposition)
    if st.session_state.groupe_selectionne:
        id_sel = st.session_state.groupe_selectionne
        info_local = st.session_state.plage.get(id_sel, {})
        num_l, num_g = id_sel.replace("L", "").split("-G")
        st.write("---")
        st.markdown(f"## Emplacement **{num_l}-{num_g}**")

        # Utilisation d'une modal pour éviter de scroller
        with st.modal(f"Éditer {id_sel}", key=f"modal_{id_sel}"):
            if info_local.get("statut", "Libre") == "Libre":
                nom = st.text_input("👤 Nom du client :", key=f"nom_client_{id_sel}")
                nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4,
                                       value=info_local.get("nb_transats", 2), key=f"nbt_{id_sel}")
                h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"), key=f"ha_{id_sel}")
                if st.button("✅ Installer le client", key=f"installer_{id_sel}", type="primary"):
                    if not nom:
                        st.error("Nom obligatoire.")
                    else:
                        st.session_state.plage[id_sel].update({
                            "statut": "Occupé", "client": nom, "nb_transats": nb_t, "heure_arrivee": h_a,
                            "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                            "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
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
                        st.session_state.groupe_selectionne = None
                        safe_rerun()
            else:
                st.markdown(
                    f"**Client :** {info_local.get('client','-')}  |  **Transats :** {info_local.get('nb_transats',2)}  |  **Arrivée :** {info_local.get('heure_arrivee','-')}")
                h_actuelle = datetime.now().strftime("%H:%M")
                h_dep = st.text_input("⏳ Heure de départ / calcul :", h_actuelle, key=f"hd_{id_sel}")
                frais_transats, heures_passees, libelle_tarif = calculer_tarif_heures(
                    info_local.get("heure_arrivee", "00:00"), h_dep, info_local.get("nb_transats", 2)
                )
                st.markdown(f"⏱️ *Temps : {heures_passees:.2f}h* — **{libelle_tarif}**")

                st.write("---")
                st.write("💰 **Règlement des Transats :**")
                if not info_local.get("transats_payes", False):
                    st.warning(f"Montant dû : {frais_transats:.2f} €")
                    if st.button("💵 Encaisser les transats DIRECT (Sur le transat)", key=f"encaisser_transat_{id_sel}"):
                        st.session_state.ca_jour = st.session_state.get("ca_jour", 0.0) + frais_transats
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
                        st.session_state.groupe_selectionne = None
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
                            st.session_state.plage[id_sel]["conso_ardoise"] = \
                                st.session_state.plage[id_sel].get("conso_ardoise", 0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                            st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi, 0) - 1
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
                        st.success("Ajouté à l'ardoise.")
                        safe_rerun()
                with col_btn_dir:
                    if st.button("⚡ Encaisser Direct", key=f"btn_dir_{id_sel}"):
                        try:
                            st.session_state.ca_jour = st.session_state.get("ca_jour", 0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["paye_direct"] = \
                                st.session_state.plage[id_sel].get("paye_direct", 0.0) + prix_unitaire
                            st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                            st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi, 0) - 1
                            nouvelle_conso = {
                                "article": produit_choisi,
                                "quantite": 1,
                                "prix_total": prix_unitaire,
                                "date": date_plan.isoformat()
                            }
                            supabase.table("consommations").insert(nouvelle_conso).execute()
                        except Exception:
                            pass
                        st.success("Encaissement direct effectué.")
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
                st.markdown(
                    f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ EN DIRECT : {info_local.get('paye_direct', 0.0) + info_local.get('prix_transats_encaisse', 0.0):.2f} €</div>",
                    unsafe_allow_html=True)
                st.markdown(
                    f"<div class='total-display'>RESTE À PAYER AU DÉPART : {total_du_final:.2f} €</div>",
                    unsafe_allow_html=True)

                col_f1, col_f2 = st.columns(2)
                if col_f1.button("💵 ENCAISSER RESTE & LIBÉRER", key=f"liberer_{id_sel}"):
                    try:
                        st.session_state.ca_jour = st.session_state.get("ca_jour", 0.0) + total_du_final
                        supabase.table("transats").update({
                            "prix": info_local.get('prix_transats_encaisse', 0.0) + transats_dus,
                            "statut_paiement": "Libre"
                        }).eq("date", date_plan.isoformat()).eq("numero_transat", id_sel).execute()
                    except Exception:
                        pass
                    st.session_state.plage[id_sel] = {
                        "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
                        "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                        "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                    }
                    st.session_state.groupe_selectionne = None
                    safe_rerun()
                if col_f2.button("Fermer", key=f"fermer_{id_sel}"):
                    st.session_state.groupe_selectionne = None
                    safe_rerun()

# ---------------------------
# RÉSERVATIONS
# ---------------------------
elif page == "📅 Réservations":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📅 GESTION DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
    st.write("---")
    col_form, col_list = st.columns([2, 3])

    # Formulaire de création
    with col_form:
        date_resa = st.date_input("Date de la réservation", value=datetime.now().date(), key="resa_date")
        preference = st.selectbox("Préférence emplacement", ["1er rang", "Allée", "Corde"], key="resa_preference")
        client_resa = st.text_input("Nom du client", key="resa_client")
        tel_resa = st.text_input("Téléphone", key="resa_tel")
        enfants = st.checkbox("Y a-t-il des enfants ?", key="resa_enfants")
        transats_resa = st.number_input("Nombre de transats", min_value=1, max_value=4, value=2, key="resa_transats")
        periode_resa = st.selectbox("Période", ["Matin", "Journée", "Après-midi"], key="resa_periode")
        if st.button("Enregistrer la réservation"):
            date_clef = date_to_key(date_resa)
            if date_clef not in st.session_state.reservations:
                st.session_state.reservations[date_clef] = []
            nouvelle = {
                "preference": preference,
                "client": client_resa,
                "telephone": tel_resa,
                "enfants": bool(enfants),
                "transats": transats_resa,
                "periode": periode_resa,
                "assigned_place": None,
                "assigned_date": None,
                "heure_arrivee": None
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

    # Liste et mini-plan pour assigner les réservations
    with col_list:
        st.markdown("### 📋 Réservations enregistrées")
        date_affiche = st.date_input("Date affichée", value=datetime.now().date(), key="resa_date_affiche")
        date_affiche_clef = date_to_key(date_affiche)

        # Mini-plan au dessus de la liste pour placer les réservés (même structure)
        st.markdown("#### Mini‑plan pour assigner les réservations")
        cols_per_line = [1,1,1,1,1,0.4,1,1,1,1,1]
        for l in range(1, 8):
            row_cols = st.columns(cols_per_line)
            for g in range(1, 6):
                id_c = f"L{l}-G{g}"
                assigned = any(
                    r.get("assigned_place") == id_c and r.get("assigned_date") == date_affiche_clef
                    for r in st.session_state.reservations.get(date_affiche_clef, [])
                )
                label = f"🟡\n{l}-{g}" if assigned else f"⚪\n{l}-{g}"
                if row_cols[g-1].button(label, key=f"resa_plan_{id_c}"):
                    st.session_state.resa_plan_place_selected = id_c
                    safe_rerun()
            with row_cols[5]:
                st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)
            for g in range(6, 11):
                id_c = f"L{l}-G{g}"
                assigned = any(
                    r.get("assigned_place") == id_c and r.get("assigned_date") == date_affiche_clef
                    for r in st.session_state.reservations.get(date_affiche_clef, [])
                )
                label = f"🟡\n{l}-{g}" if assigned else f"⚪\n{l}-{g}"
                if row_cols[g].button(label, key=f"resa_plan_{id_c}_r"):
                    st.session_state.resa_plan_place_selected = id_c
                    safe_rerun()

        # Si une place du mini-plan est sélectionnée, afficher les réservations candidates pour assignation
        if st.session_state.resa_plan_place_selected:
            place_sel = st.session_state.resa_plan_place_selected
            st.write("---")
            st.markdown(f"#### Réservations candidates pour la place {place_sel} ({date_affiche_clef})")
            listes = st.session_state.reservations.get(date_affiche_clef, [])
            candidats = []
            for idx, rr in enumerate(listes):
                # on propose les réservations non assignées ou déjà assignées à cette place
                if rr.get("assigned_place") in (None, place_sel):
                    candidats.append((idx, rr))
            if not candidats:
                st.info("Aucune réservation correspondante pour cette place.")
            else:
                for idx, rr in candidats:
                    st.write(
                        f"- **{rr.get('client','-')}** — {rr.get('transats')} transats — Préf: {rr.get('preference')} — "
                        f"Tel: {rr.get('telephone','-')} — Enfants: {'Oui' if rr.get('enfants') else 'Non'} — "
                        f"Emplacement: {rr.get('assigned_place') or 'Non assigné'}"
                    )
                    col1, col2 = st.columns([1,1])
                    if col1.button("Assigner ici", key=f"assign_here_{place_sel}_{idx}"):
                        # assigner la réservation à la place pour la date affichée
                        st.session_state.reservations[date_affiche_clef][idx]["assigned_place"] = place_sel
                        st.session_state.reservations[date_affiche_clef][idx]["assigned_date"] = date_affiche_clef
                        # on peut aussi stocker heure d'arrivée prévue si besoin
                        st.success(f"{rr.get('client')} assigné(e) à {place_sel} pour le {date_affiche_clef}.")
                        safe_rerun()
                    if col2.button("Voir détails", key=f"voir_det_{place_sel}_{idx}"):
                        st.write(rr)

        st.write("---")
        st.markdown(f"### Réservations pour {date_affiche_clef}")
        listes = st.session_state.reservations.get(date_affiche_clef, [])
        if not listes:
            st.info("Aucune réservation pour cette date.")
        else:
            for i, r in enumerate(listes):
                assigned = r.get("assigned_place")
                st.write(
                    f"**{r.get('client','-')}** — {r.get('transats')} transats — {r.get('periode')} — "
                    f"Préf : {r.get('preference')} — Tel: {r.get('telephone','-')} — "
                    f"Enfants: {'Oui' if r.get('enfants') else 'Non'} — Emplacement: {assigned or 'Non assigné'}"
                )
                col_a, col_b, col_c = st.columns([1,1,1])

                if col_a.button("Annuler", key=f"annuler_resa_{date_affiche_clef}_{i}"):
                    resa = st.session_state.reservations[date_affiche_clef].pop(i)
                    try:
                        # tentative suppression côté supabase si présent
                        rep = supabase.table("reservations").select("*") \
                            .eq("date", date_affiche.isoformat()) \
                            .eq("nom_client", resa["client"]).execute()
                        rows = rep.data or []
                        for row in rows:
                            supabase.table("reservations").delete().eq("id", row.get("id")).execute()
                    except Exception:
                        pass
                    st.success("Réservation annulée.")
                    safe_rerun()

                if col_b.button("Modifier", key=f"modif_resa_{date_affiche_clef}_{i}"):
                    # affichage d'un petit formulaire inline pour modification
                    with st.expander(f"Modifier {r.get('client')}"):
                        new_pref = st.selectbox("Nouvelle préférence", ["1er rang", "Allée", "Corde"],
                                                index=["1er rang","Allée","Corde"].index(r.get("preference","1er rang")),
                                                key=f"mod_pref_{date_affiche_clef}_{i}")
                        new_tel = st.text_input("Téléphone", value=r.get("telephone", ""), key=f"mod_tel_{date_affiche_clef}_{i}")
                        new_enf = st.checkbox("Enfants ?", value=r.get("enfants", False), key=f"mod_enf_{date_affiche_clef}_{i}")
                        new_trans = st.number_input("Nombre de transats", min_value=1, max_value=4,
                                                    value=r.get("transats", 2),
                                                    key=f"mod_trans_{date_affiche_clef}_{i}")
                        if st.button("Valider modification", key=f"valider_modif_{date_affiche_clef}_{i}"):
                            st.session_state.reservations[date_affiche_clef][i].update({
                                "preference": new_pref,
                                "telephone": new_tel,
                                "enfants": bool(new_enf),
                                "transats": new_trans
                            })
                            try:
                                # tentative update supabase
                                rep = supabase.table("reservations").select("*") \
                                    .eq("date", date_affiche.isoformat()) \
                                    .eq("nom_client", r.get("client")).execute()
                                rows = rep.data or []
                                if rows:
                                    supabase.table("reservations").update({
                                        "preference": new_pref,
                                        "telephone": new_tel,
                                        "enfants": bool(new_enf),
                                        "transats": new_trans
                                    }).eq("id", rows[0].get("id")).execute()
                            except Exception:
                                pass
                            st.success("Réservation modifiée.")
                            safe_rerun()

                if col_c.button("Assigner sur plan", key=f"assign_on_plan_{date_affiche_clef}_{i}"):
                    # on ouvre un mini sélecteur de place pour assigner directement
                    st.session_state.resa_plan_place_selected = None
                    st.session_state._assign_target = (date_affiche_clef, i)
                    st.info("Choisis une place dans le mini‑plan ci‑dessus pour assigner cette réservation.")
                    safe_rerun()

# ---------------------------
# PÉDALOS
# ---------------------------
elif page == "🛶 Pédalos":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>🛶 PÉDALOS</h3>", unsafe_allow_html=True)
    st.write("---")
    # Affichage simple avec séparation entre pédalos
    for idx, (k, v) in enumerate(st.session_state.pedalos.items(), start=1):
        st.markdown(f"**{k}** — {v.get('statut','Disponible')} — Client: {v.get('client','-')}")
        st.markdown("<div class='pedalo-sep'></div>", unsafe_allow_html=True)

# ---------------------------
# STOCKS & FRIGOS
# ---------------------------
elif page == "📦 Stocks & Frigos":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📦 STOCKS</h3>", unsafe_allow_html=True)
    st.write("---")
    for key in list(st.session_state.stocks.keys()):
        col1, col2 = st.columns([2,1])
        with col1:
            st.write(f"**{key}**")
        with col2:
            # boutons -1, +1, +10
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            if c1.button("-1", key=f"stock_minus1_{key}"):
                st.session_state.stocks[key] = max(0, st.session_state.stocks.get(key,0) - 1)
                safe_rerun()
            if c2.button("+1", key=f"stock_plus1_{key}"):
                st.session_state.stocks[key] = st.session_state.stocks.get(key,0) + 1
                safe_rerun()
            if c3.button("+10", key=f"stock_plus10_{key}"):
                st.session_state.stocks[key] = st.session_state.stocks.get(key,0) + 10
                safe_rerun()
            # clic sur le nombre pour modifier précisément
            if c4.button(f"{st.session_state.stocks.get(key,0)}", key=f"stock_set_{key}"):
                # ouvrir modal pour entrer la valeur précise
                val = st.number_input(f"Entrer la quantité pour {key}", min_value=0, value=st.session_state.stocks.get(key,0), key=f"input_stock_{key}")
                if st.button("Valider", key=f"valider_stock_{key}"):
                    st.session_state.stocks[key] = int(val)
                    st.success("Stock mis à jour.")
                    safe_rerun()

# ---------------------------
# CHIFFRE D'AFFAIRES (simple)
# ---------------------------
elif page == "📊 Chiffre d'Affaires":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📊 CHIFFRE D'AFFAIRES</h3>", unsafe_allow_html=True)
    st.write("---")
    st.metric("CA du jour", f"{st.session_state.get('ca_jour',0.0):.2f} €")

# ---------------------------
# RÉCAP JOURNALIER (simple)
# ---------------------------
elif page == "📊 Récap Journalier":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📋 RÉCAP JOURNALIER</h3>", unsafe_allow_html=True)
    st.write("---")
    st.write("Notes et résumé rapide")
    for n in st.session_state.notes:
        st.write(f"- {n}")

# ---------------------------
# NOTES (To-Do)
# ---------------------------
elif page == "📝 Notes (To-Do List)":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>📝 NOTES</h3>", unsafe_allow_html=True)
    new_note = st.text_input("Nouvelle note", key="new_note")
    if st.button("Ajouter note"):
        if new_note:
            st.session_state.notes.append(new_note)
            st.success("Note ajoutée.")
            safe_rerun()
    for i, note in enumerate(st.session_state.notes):
        st.write(f"- {note}  ", end="")
        if st.button("Supprimer", key=f"del_note_{i}"):
            st.session_state.notes.pop(i)
            safe_rerun()

# ---------------------------
# FIN
# ---------------------------
else:
    st.write("Page non implémentée.")
