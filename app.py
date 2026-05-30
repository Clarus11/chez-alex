import streamlit as st
from datetime import datetime, date
from supabase import create_client
import json

# =========================================================
# 1. CONFIG GÉNÉRALE & STYLE
# =========================================================
st.set_page_config(page_title="Chez Alex 2026", page_icon="🏖️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfaf3; }

    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 3px !important;
        align-items: center !important;
        padding: 0 !important;
    }

    .stButton > button {
        width: 100% !important;
        height: 55px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }

    .stButton > button:hover { transform: scale(1.02); }

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

# =========================================================
# 2. CONNEXION SUPABASE & OUTILS DE SAUVEGARDE
# =========================================================
if "supabase_ready" not in st.session_state:
    st.session_state.supabase_ready = False
    st.session_state.supabase = None

try:
    url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key:
        supabase = create_client(url, key)
        st.session_state.supabase = supabase
        st.session_state.supabase_ready = True
    else:
        st.warning("Mode sauvegarde locale activé (pas de clés Supabase).")
except Exception:
    st.warning("Mode sauvegarde locale activé (erreur de connexion Supabase).")

def sauvegarder_etat_global(cle: str, valeur):
    """
    Sauvegarde un bloc d'état (dict, liste, nombre...) dans une table générique 'etat_site'.
    Table attendue côté Supabase :
        - cle   : text (PRIMARY KEY ou unique)
        - valeur: text (JSON)
    """
    if not st.session_state.supabase_ready:
        return
    try:
        data_json = json.dumps(valeur)
        st.session_state.supabase.table("etat_site").upsert(
            {"cle": cle, "valeur": data_json}
        ).execute()
    except Exception as e:
        st.error(f"Erreur sauvegarde état global ({cle}) : {e}")

def charger_etat_global(cle: str, defaut):
    """
    Charge un bloc d'état depuis 'etat_site'.
    Si rien en base ou erreur → renvoie la valeur par défaut.
    """
    if not st.session_state.supabase_ready:
        return defaut
    try:
        res = st.session_state.supabase.table("etat_site").select("*").eq("cle", cle).execute()
        if res.data:
            return json.loads(res.data[0]["valeur"])
        return defaut
    except Exception:
        return defaut

# =========================================================
# 3. RÉSERVATIONS : OUTILS SUPABASE
# =========================================================
def charger_reservations(date_cible: date):
    """
    Charge toutes les réservations pour une date donnée (table 'reservations').
    Table attendue côté Supabase :
        - id (PK)
        - client, telephone
        - transats (int)
        - preference (text)
        - emplacement (text)
        - est_place (bool)
        - date_resa (text, format YYYY-MM-DD)
        - statut (text)
        - heure_arrivee, heure_depart (text HH:MM)
        - montant (float)
        - transats_payes (bool)
        - conso_ardoise (float)
        - paye_direct (float)
        - historique_conso (json/text)
    """
    if not st.session_state.supabase_ready:
        return st.session_state.get("reservations_local", {}).get(str(date_cible), [])
    try:
        res = st.session_state.supabase.table("reservations").select("*").eq("date_resa", str(date_cible)).execute()
        return res.data or []
    except Exception:
        return st.session_state.get("reservations_local", {}).get(str(date_cible), [])

def sauvegarder_reservation(data: dict):
    """
    Insert / update d'une réservation dans Supabase + copie locale de secours.
    """
    # Sauvegarde Supabase
    if st.session_state.supabase_ready:
        try:
            if "id" in data and data["id"]:
                st.session_state.supabase.table("reservations").update(data).eq("id", data["id"]).execute()
            else:
                res = st.session_state.supabase.table("reservations").insert(data).execute()
                if res.data:
                    data["id"] = res.data[0]["id"]
        except Exception as e:
            st.error(f"Erreur Supabase (reservations) : {e}")

    # Copie locale de secours
    if "reservations_local" not in st.session_state:
        st.session_state.reservations_local = {}
    jour = data.get("date_resa", str(date.today()))
    if jour not in st.session_state.reservations_local:
        st.session_state.reservations_local[jour] = []

    if "id" in data and data["id"]:
        updated = False
        for i, r in enumerate(st.session_state.reservations_local[jour]):
            if r.get("id") == data["id"]:
                st.session_state.reservations_local[jour][i] = data
                updated = True
                break
        if not updated:
            st.session_state.reservations_local[jour].append(data)
    else:
        data["id"] = len(st.session_state.reservations_local[jour]) + 1
        st.session_state.reservations_local[jour].append(data)

# =========================================================
# 4. CALCUL TARIFAIRE (TRANSATS)
# =========================================================
def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    """
    Calcule le tarif en fonction du temps passé :
        - ≤ 2h  → 7€/transat
        - ≤ 5h  → 12€/transat
        - > 5h  → 15€/transat
    Retourne : (montant_total, heures_passées, libellé)
    """
    try:
        t1 = datetime.strptime(heure_arr.strip(), "%H:%M")
        t2 = datetime.strptime(heure_dep.strip(), "%H:%M")
        diff = t2 - t1
        minutes = diff.total_seconds() / 60
        if minutes <= 0:
            return 0.0, 0.0, "Temps invalide"
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
    except Exception:
        return 15.0 * nb_transats, 0.0, "Tarif Journée (défaut)"
# =========================================================
# 5. SÉCURITÉ D'ACCÈS
# =========================================================
if "autorise" not in st.session_state:
    st.session_state.autorise = False

mdp_secret = st.secrets.get("password", "alex2026")

if not st.session_state.autorise:
    st.markdown("<h2 style='text-align: center; color: #854d0e; margin-top:80px;'>🏖️ Chez Alex - Équipe</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp = st.text_input("Mot de passe d'accès :", type="password")
        if st.button("Ouvrir l'application 🔓", type="primary", use_container_width=True):
            if mdp == mdp_secret:
                st.session_state.autorise = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    st.stop()

# =========================================================
# 6. TARIFS CONSOMMATIONS (BAR / SNACK)
# =========================================================
TARIFS_CONSO = {
    "Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50,
    "Oasis Tropical": 2.50, "Tropico": 2.50, "Fanta Orange": 2.50, "Fanta Citron": 2.50,
    "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Jus Orange Pressé": 5.00,
    "Virgin Mojito": 6.00, "Glace Artisanale": 3.80
}

# =========================================================
# 7. INITIALISATION DES STRUCTURES EN MÉMOIRE
# =========================================================

# --- PLAN DE LA PLAGE (140 EMPLACEMENTS) ---
if "plage" not in st.session_state:
    plage_defaut = {}
    for l in range(1, 8):          # 7 lignes
        for g in range(1, 11):     # 10 groupes par ligne
            id_c = f"L{l}-G{g}"
            plage_defaut[id_c] = {
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
    # On tente de charger depuis Supabase, sinon on garde le défaut
    st.session_state.plage = charger_etat_global("plage", plage_defaut)

# --- FLOTTE DE PÉDALOS ---
if "pedalos" not in st.session_state:
    ped_defaut = {}
    for p in range(1, 6):
        ped_defaut[f"Pédalo {p}"] = {
            "statut": "Disponible",
            "client": "",
            "heure_depart": "",
            "duree_prevue": "1h",
            "total_du": 0.0
        }
    st.session_state.pedalos = charger_etat_global("pedalos", ped_defaut)

# --- STOCKS ---
if "stocks" not in st.session_state:
    stocks_defaut = {
        # Tu peux adapter ces catégories ou les remplacer par les produits unitaires
        "Coca-Cola": 50,
        "Coca-Cola Zero": 50,
        "Orangina": 40,
        "Schweppes Agrume": 40,
        "Oasis Tropical": 40,
        "Tropico": 40,
        "Fanta Orange": 40,
        "Fanta Citron": 40,
        "Petite Eau": 100,
        "Grande Eau": 60,
        "Café / Thé": 200,
        "Jus Orange Pressé": 40,
        "Virgin Mojito": 30,
        "Glace Artisanale": 60
    }
    st.session_state.stocks = charger_etat_global("stocks", stocks_defaut)

# --- NOTES / CAHIER DE LIAISON ---
if "notes" not in st.session_state:
    st.session_state.notes = charger_etat_global("notes", [])

# --- CHIFFRE D'AFFAIRES JOURNALIER ---
if "ca_jour" not in st.session_state:
    st.session_state.ca_jour = charger_etat_global("ca_jour", 0.0)

# --- RÉSERVATIONS (CACHE LOCAL EN PLUS DE SUPABASE) ---
if "reservations" not in st.session_state:
    st.session_state.reservations = {}

# --- SÉLECTIONS COURANTES (UI) ---
if "groupe_selectionne" not in st.session_state:
    st.session_state.groupe_selectionne = None

if "pedalo_selectionne" not in st.session_state:
    st.session_state.pedalo_selectionne = None
# =========================================================
# 8. NAVIGATION LATÉRALE
# =========================================================
with st.sidebar:
    st.markdown("<h2 style='color: #854d0e; text-align: center;'>CHEZ ALEX</h2>", unsafe_allow_html=True)
    st.write("---")

    date_travail = st.date_input("📆 Date d'exploitation :", date.today())

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

# Chargement des réservations du jour
resas_du_jour = charger_reservations(date_travail)

# =========================================================
# 9. MODULE : PLAN DE LA PLAGE
# =========================================================
if page == "🏖️ Plan de la plage":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
    st.write("")

    # Injection automatique des réservations du jour
    for resa in resas_du_jour:
        place = resa.get("emplacement")
        if not place:
            continue

        # Normalisation : "1-3" → "L1-G3"
        if "-" in place and not place.startswith("L"):
            l, g = place.split("-")
            place_norm = f"L{l}-G{g}"
        else:
            place_norm = place

        if place_norm in st.session_state.plage and st.session_state.plage[place_norm]["statut"] == "Libre":
            st.session_state.plage[place_norm].update({
                "statut": "Occupé",
                "client": resa["client"],
                "nb_transats": resa.get("transats", 2),
                "heure_arrivee": resa.get("heure_arrivee", "09:00"),
                "transats_payes": resa.get("transats_payes", False),
                "conso_ardoise": resa.get("conso_ardoise", 0.0),
                "historique_conso": resa.get("historique_conso", []),
                "paye_direct": resa.get("paye_direct", 0.0),
                "historique_paye_direct": []
            })

    # --- AFFICHAGE DES 140 EMPLACEMENTS ---
    for l in range(1, 8):
        st.caption(f"Ligne {l}")
        cols = st.columns([1,1,1,1,1,0.4,1,1,1,1,1])

        # Groupes 1 à 5
        for g in range(1, 6):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
            if cols[g-1].button(label, key=id_c, type="secondary" if info["statut"]=="Libre" else "primary"):
                st.session_state.groupe_selectionne = id_c
                st.rerun()

        # Allée centrale
        with cols[5]:
            st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

        # Groupes 6 à 10
        for g in range(6, 11):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info["statut"] == "Libre" else f"🔴\n{info['client']}"
            if cols[g].button(label, key=id_c, type="secondary" if info["statut"]=="Libre" else "primary"):
                st.session_state.groupe_selectionne = id_c
                st.rerun()

    # =========================================================
    # 10. FENÊTRE DE GESTION D’UN EMPLACEMENT
    # =========================================================
    if st.session_state.groupe_selectionne:

        @st.dialog("Gestion de l'emplacement")
        def gerer_place(id_sel):

            info = st.session_state.plage[id_sel]

            # Sécurisation des clés
            for k, v in {
                "historique_conso": [],
                "historique_paye_direct": [],
                "paye_direct": 0.0,
                "conso_ardoise": 0.0
            }.items():
                if k not in info:
                    info[k] = v

            num_l, num_g = id_sel.replace("L","").split("-G")
            st.markdown(f"### Emplacement **{num_l}-{num_g}**")

            # --- CAS 1 : EMPLACEMENT LIBRE ---
            if info["statut"] == "Libre":
                nom = st.text_input("👤 Nom du client :")
                nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=2)
                h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"))

                if st.button("Installer le client", type="primary"):
                    if nom.strip():
                        info.update({
                            "statut": "Occupé",
                            "client": nom,
                            "nb_transats": nb_t,
                            "heure_arrivee": h_a,
                            "transats_payes": False,
                            "prix_transats_encaisse": 0.0,
                            "conso_ardoise": 0.0,
                            "historique_conso": [],
                            "paye_direct": 0.0,
                            "historique_paye_direct": []
                        })

                        # Création d'une réservation "passage"
                        nouvelle_resa = {
                            "client": nom,
                            "telephone": "Passage",
                            "transats": int(nb_t),
                            "preference": "",
                            "emplacement": f"{num_l}-{num_g}",
                            "est_place": True,
                            "date_resa": str(date_travail),
                            "statut": "Occupé",
                            "heure_arrivee": h_a,
                            "heure_depart": "",
                            "montant": 0.0,
                            "transats_payes": False,
                            "conso_ardoise": 0.0,
                            "paye_direct": 0.0,
                            "historique_conso": []
                        }
                        sauvegarder_reservation(nouvelle_resa)
                        sauvegarder_etat_global("plage", st.session_state.plage)

                        st.session_state.groupe_selectionne = None
                        st.rerun()
                    else:
                        st.error("Nom obligatoire.")

            # --- CAS 2 : EMPLACEMENT OCCUPÉ ---
            else:
                st.markdown(f"👤 **{info['client']}**")
                st.markdown(f"🪑 {info['nb_transats']} transats")
                st.markdown(f"⏰ Arrivée : {info['heure_arrivee']}")

                h_dep = st.text_input("⏳ Heure de départ :", datetime.now().strftime("%H:%M"))
                montant, heures, libelle = calculer_tarif_heures(info["heure_arrivee"], h_dep, info["nb_transats"])

                st.info(f"{libelle} — Temps : {heures:.2f}h")

                # --- Paiement transats ---
                st.write("### 💰 Paiement des transats")
                if not info["transats_payes"]:
                    st.warning(f"Montant dû : {montant:.2f} €")
                    if st.button("Encaisser transats"):
                        info["transats_payes"] = True
                        info["prix_transats_encaisse"] = montant
                        st.session_state.ca_jour += montant
                        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                        sauvegarder_etat_global("plage", st.session_state.plage)
                        st.rerun()
                else:
                    st.success(f"Transats déjà réglés ({info['prix_transats_encaisse']:.2f} €)")

                # --- Consommations ---
                st.write("### 🛒 Ajouter une consommation")
                produit = st.selectbox("Produit :", list(TARIFS_CONSO.keys()))
                prix = TARIFS_CONSO[produit]

                colA, colB = st.columns(2)
                if colA.button("Ajouter à l'ardoise"):
                    info["conso_ardoise"] += prix
                    info["historique_conso"].append(f"{produit} (Ardoise)")
                    st.session_state.stocks[produit] = max(0, st.session_state.stocks.get(produit, 0) - 1)
                    sauvegarder_etat_global("stocks", st.session_state.stocks)
                    sauvegarder_etat_global("plage", st.session_state.plage)
                    st.rerun()

                if colB.button("Encaisser direct"):
                    info["paye_direct"] += prix
                    info["historique_paye_direct"].append(f"{produit} (Direct)")
                    st.session_state.ca_jour += prix
                    st.session_state.stocks[produit] = max(0, st.session_state.stocks.get(produit, 0) - 1)
                    sauvegarder_etat_global("stocks", st.session_state.stocks)
                    sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                    sauvegarder_etat_global("plage", st.session_state.plage)
                    st.rerun()

                # --- Récap conso ---
                if info["historique_conso"] or info["historique_paye_direct"]:
                    with st.expander("Voir les consommations"):
                        for c in info["historique_conso"]:
                            st.write("⏳", c)
                        for c in info["historique_paye_direct"]:
                            st.write("💵", c)

                # --- Total final ---
                reste_transats = 0 if info["transats_payes"] else montant
                total_final = reste_transats + info["conso_ardoise"]

                st.markdown(f"<div class='paye-direct-display'>Déjà encaissé : {info['paye_direct'] + info['prix_transats_encaisse']:.2f} €</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='total-display'>Reste à payer : {total_final:.2f} €</div>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                if col1.button("Encaisser & libérer", type="primary"):
                    st.session_state.ca_jour += total_final
                    st.session_state.plage[id_sel] = {
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
                    sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                    sauvegarder_etat_global("plage", st.session_state.plage)
                    st.session_state.groupe_selectionne = None
                    st.rerun()

                if col2.button("Fermer"):
                    st.session_state.groupe_selectionne = None
                    st.rerun()

        gerer_place(st.session_state.groupe_selectionne)
# =========================================================
# 11. MODULE : PÉDALOS
# =========================================================
elif page == "🚣 Pédalos":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>🚣 GESTION DE LA FLOTTE DE PÉDALOS</h3>", unsafe_allow_html=True)
    st.write("Suivi des départs en mer, durées, retours et encaissements.")
    st.write("---")

    # --- AFFICHAGE DES 5 PÉDALOS ---
    for p_id, p_info in st.session_state.pedalos.items():
        with st.container(border=True):
            col_p1, col_p2, col_p3 = st.columns([2, 4, 3])

            # --- COLONNE 1 : ÉTAT ---
            with col_p1:
                if p_info["statut"] == "Disponible":
                    st.markdown(f"### 🔵 {p_id}")
                    st.success("Disponible")
                else:
                    st.markdown(f"### 🚣 {p_id}")
                    st.error("En Mer")

            # --- COLONNE 2 : INFORMATIONS ---
            with col_p2:
                if p_info["statut"] == "Disponible":
                    nom_p = st.text_input("Nom du client :", key=f"nom_{p_id}", placeholder="Ex: Lucas")
                    duree_p = st.radio("Durée demandée :", ["30 min (15€)", "1h (20€)", "2h (35€)"], key=f"dur_{p_id}", horizontal=True)
                    h_dep_p = st.text_input("Heure de départ :", datetime.now().strftime("%H:%M"), key=f"hdep_{p_id}")
                else:
                    st.markdown(f"👤 **Client :** {p_info['client']}")
                    st.markdown(f"⏰ **Départ :** {p_info['heure_depart']}")
                    st.markdown(f"🕒 **Durée prévue :** {p_info['duree_prevue']}")
                    st.markdown(f"💰 **Montant dû :** {p_info['total_du']:.2f} €")

            # --- COLONNE 3 : ACTIONS ---
            with col_p3:
                st.write("")

                # --- LANCER UN PÉDALO ---
                if p_info["statut"] == "Disponible":
                    if st.button("🚀 Mettre à l'eau", key=f"btn_l_{p_id}", type="primary", use_container_width=True):
                        if nom_p.strip():
                            # Détermination du prix
                            if "30 min" in duree_p:
                                prix_p = 15.0
                            elif "2h" in duree_p:
                                prix_p = 35.0
                            else:
                                prix_p = 20.0

                            st.session_state.pedalos[p_id].update({
                                "statut": "En Mer",
                                "client": nom_p.strip(),
                                "heure_depart": h_dep_p,
                                "duree_prevue": duree_p,
                                "total_du": prix_p
                            })

                            # Sauvegarde Supabase
                            sauvegarder_etat_global("pedalos", st.session_state.pedalos)

                            st.rerun()
                        else:
                            st.error("Veuillez entrer un nom.")

                # --- RETOUR & ENCAISSEMENT ---
                else:
                    if st.button("💵 Retour & Encaisser", key=f"btn_r_{p_id}", type="primary", use_container_width=True):
                        st.session_state.ca_jour += p_info["total_du"]

                        # Remise à zéro
                        st.session_state.pedalos[p_id] = {
                            "statut": "Disponible",
                            "client": "",
                            "heure_depart": "",
                            "duree_prevue": "1h",
                            "total_du": 0.0
                        }

                        # Sauvegardes
                        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                        sauvegarder_etat_global("pedalos", st.session_state.pedalos)

                        st.success(f"Pédalo {p_id} libéré et encaissement effectué.")
                        st.rerun()
# =========================================================
# 12. MODULE : GESTION DES STOCKS & FRIGOS
# =========================================================
elif page == "📦 Stocks & Frigos":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📦 GESTION DES STOCKS & FRIGOS</h3>", unsafe_allow_html=True)
    st.write("---")

    st.info("💡 Les stocks diminuent automatiquement à chaque vente (ardoise ou direct) sur le plan de la plage.")

    # En-tête du tableau
    col_h1, col_h2, col_h3 = st.columns([3, 1.5, 2])
    with col_h1:
        st.markdown("**Produit**")
    with col_h2:
        st.markdown("**Quantité en réserve**")
    with col_h3:
        st.markdown("**Ajouter du stock (Réassort)**")
    st.write("---")

    # On boucle sur tous les produits connus dans les tarifs
    for produit in TARIFS_CONSO.keys():
        if produit not in st.session_state.stocks:
            st.session_state.stocks[produit] = 0

        quantite_actuelle = st.session_state.stocks[produit]

        col_nom, col_qte, col_actions = st.columns([3, 1.5, 2])

        with col_nom:
            st.write(f"🍹 {produit}")

        with col_qte:
            if quantite_actuelle <= 5:
                st.markdown(
                    f"<b style='color: #dc2626;'>{quantite_actuelle} ⚠️ (Bas)</b>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<b style='color: #16a34a;'>{quantite_actuelle}</b>",
                    unsafe_allow_html=True
                )

        with col_actions:
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("➕ 1", key=f"plus1_{produit}", use_container_width=True):
                st.session_state.stocks[produit] += 1
                sauvegarder_etat_global("stocks", st.session_state.stocks)
                st.rerun()
            if btn_col2.button("➕ 10", key=f"plus10_{produit}", use_container_width=True):
                st.session_state.stocks[produit] += 10
                sauvegarder_etat_global("stocks", st.session_state.stocks)
                st.rerun()

    st.write("---")
# =========================================================
# 13. MODULE : NOTES (TO-DO LIST)
# =========================================================
elif page == "📝 Notes (To-Do List)":
    st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
    st.write("")

    # --- AJOUT D’UNE NOTE ---
    col_note, col_btn = st.columns([4, 1])
    nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Nettoyer la ligne 3")

    if col_btn.button("Ajouter", use_container_width=True):
        if nouvelle_note.strip():
            st.session_state.notes.append(nouvelle_note.strip())
            sauvegarder_etat_global("notes", st.session_state.notes)
            st.rerun()
        else:
            st.error("Veuillez entrer une note valide.")

    st.write("---")

    # --- LISTE DES NOTES AVEC SUPPRESSION ---
    notes_a_supprimer = []

    if not st.session_state.notes:
        st.info("Aucune note pour le moment.")
    else:
        for i, note in enumerate(st.session_state.notes):
            if st.checkbox(note, key=f"note_{i}"):
                notes_a_supprimer.append(i)

    # Suppression des notes cochées
    if notes_a_supprimer:
        for i in reversed(notes_a_supprimer):
            st.session_state.notes.pop(i)

        sauvegarder_etat_global("notes", st.session_state.notes)
        st.rerun()
# =========================================================
# 14. MODULE : CHIFFRE D'AFFAIRES
# =========================================================
elif page == "📊 Chiffre d'Affaires":
    st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
    st.write("")

    # Affichage du CA du jour
    st.metric("Total encaissé aujourd'hui", f"{st.session_state.ca_jour:.2f} €")

    st.write("---")

    # Bouton pour remettre à zéro (optionnel)
    if st.button("🔄 Remettre le compteur du jour à zéro"):
        st.session_state.ca_jour = 0.0
        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
        st.success("Le chiffre d'affaires du jour a été remis à zéro.")
        st.rerun()
# =========================================================
# 15. MODULE : RÉSERVATIONS (REGISTRE COMPLET)
# =========================================================
elif page == "📅 Réservations":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📅 GESTION & REGISTRE DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
    st.write("---")

    # =====================================================
    # FORMULAIRE D’AJOUT D’UNE RÉSERVATION PLANIFIÉE
    # =====================================================
    with st.form("form_nouvelle_resa"):
        st.markdown("### ➕ Ajouter une réservation planifiée")

        col1, col2, col3 = st.columns([2, 1, 1])
        nom_c = col1.text_input("Nom du client :")
        tel_c = col2.text_input("Téléphone :")
        nb_tr = col3.number_input("Nombre de transats :", min_value=1, max_value=10, value=2)

        col4, col5, col6 = st.columns(3)
        h_ar = col4.text_input("Heure d'arrivée prévue :", "10:00")
        h_de = col5.text_input("Heure de départ prévue :", "18:00")
        pref = col6.text_input("Préférence (ex : Ligne 1, Allée...)")

        if st.form_submit_button("Enregistrer la réservation", type="primary"):
            if nom_c.strip():
                montant, _, _ = calculer_tarif_heures(h_ar, h_de, nb_tr)

                nouvelle_resa = {
                    "client": nom_c.strip(),
                    "telephone": tel_c.strip(),
                    "transats": int(nb_tr),
                    "preference": pref.strip(),
                    "emplacement": "",
                    "est_place": False,
                    "date_resa": str(date_travail),
                    "statut": "Confirmé",
                    "heure_arrivee": h_ar,
                    "heure_depart": h_de,
                    "montant": montant,
                    "transats_payes": False,
                    "conso_ardoise": 0.0,
                    "paye_direct": 0.0,
                    "historique_conso": []
                }

                sauvegarder_reservation(nouvelle_resa)
                st.success(f"Réservation enregistrée pour {nom_c} ({montant:.2f} €).")
                st.rerun()
            else:
                st.error("Le nom du client est obligatoire.")

    st.write("---")

    # =====================================================
    # LISTE DES RÉSERVATIONS DU JOUR
    # =====================================================
    st.markdown("### 📋 Réservations du jour")

    if not resas_du_jour:
        st.info("Aucune réservation pour cette date.")
    else:
        for resa in resas_du_jour:
            colA, colB = st.columns([4, 1])

            with colA:
                statut = "📍 Placé" if resa.get("est_place") else "⏳ En attente"
                emplacement = resa.get("emplacement") or "—"

                st.markdown(
                    f"""
                    **{resa['client']}**  
                    • {resa['transats']} transats  
                    • {resa['heure_arrivee']} → {resa['heure_depart']}  
                    • Emplacement : `{emplacement}`  
                    • Statut : **{statut}**
                    """
                )

            with colB:
                if not resa.get("est_place"):
                    # Permet d'attribuer un emplacement manuellement
                    new_place = st.text_input(
                        "Attribuer emplacement (ex: 1-3)",
                        key=f"pl_{resa['id']}"
                    )
                    if st.button("Placer", key=f"btn_place_{resa['id']}"):
                        if new_place.strip():
                            # Normalisation
                            if "-" in new_place and not new_place.startswith("L"):
                                l, g = new_place.split("-")
                                new_place_norm = f"L{l}-G{g}"
                            else:
                                new_place_norm = new_place

                            resa["emplacement"] = new_place_norm
                            resa["est_place"] = True
                            resa["statut"] = "Occupé"

                            sauvegarder_reservation(resa)
                            st.success(f"{resa['client']} placé en {new_place_norm}.")
                            st.rerun()
                        else:
                            st.error("Veuillez entrer un emplacement valide.")
