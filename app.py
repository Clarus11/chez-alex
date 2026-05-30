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
        st.warning("Mode sauvegarde locale (pas de clés Supabase).")
except Exception:
    st.warning("Mode sauvegarde locale (erreur de connexion Supabase).")

def sauvegarder_etat_global(cle: str, valeur):
    """Sauvegarde un bloc d'état (JSON) dans une table générique 'etat_site'."""
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
    """Charge un bloc d'état (JSON) depuis 'etat_site'."""
    if not st.session_state.supabase_ready:
        return defaut
    try:
        res = st.session_state.supabase.table("etat_site").select("*").eq("cle", cle).execute()
        if res.data:
            return json.loads(res.data[0]["valeur"])
        return defaut
    except Exception:
        return defaut

# Réservations : on réutilise la logique du deuxième code (table 'reservations')
def charger_reservations(date_cible: date):
    if not st.session_state.supabase_ready:
        # fallback : on garde aussi une copie locale si besoin
        return st.session_state.get("reservations_local", {}).get(str(date_cible), [])
    try:
        res = st.session_state.supabase.table("reservations").select("*").eq("date_resa", str(date_cible)).execute()
        return res.data or []
    except Exception:
        return st.session_state.get("reservations_local", {}).get(str(date_cible), [])

def sauvegarder_reservation(data: dict):
    # Supabase
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
    # mise à jour ou ajout
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
# 3. CALCUL TARIFAIRE
# =========================================================
def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
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
# 4. SÉCURITÉ D'ACCÈS
# =========================================================
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
    st.stop()

# =========================================================
# 5. INITIALISATION DES STRUCTURES (AVEC CHARGEMENT SUPABASE)
# =========================================================
# Tarifs conso
TARIFS_CONSO = {
    "Coca-Cola": 2.50, "Coca-Cola Zero": 2.50, "Orangina": 2.50, "Schweppes Agrume": 2.50,
    "Oasis Tropical": 2.50, "Tropico": 2.50, "Fanta Orange": 2.50, "Fanta Citron": 2.50,
    "Petite Eau": 1.50, "Grande Eau": 2.50, "Café / Thé": 1.00, "Jus Orange Pressé": 5.00,
    "Virgin Mojito": 6.00, "Glace Artisanale": 3.80
}

# Plage (140 emplacements)
if "plage" not in st.session_state:
    plage_defaut = {}
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            plage_defaut[id_c] = {
                "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
                "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
            }
    st.session_state.plage = charger_etat_global("plage", plage_defaut)

# Pédalos
if "pedalos" not in st.session_state:
    ped_defaut = {}
    for p in range(1, 6):
        ped_defaut[f"Pédalo {p}"] = {
            "statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0
        }
    st.session_state.pedalos = charger_etat_global("pedalos", ped_defaut)

# Stocks
if "stocks" not in st.session_state:
    stocks_defaut = {
        "Boissons & Cafés": 150,
        "Oranges (Jus)": 40,
        "Menthe & Citrons (Mojito)": 30,
        "Glaces Artisanales": 60
    }
    # on ajoute aussi chaque produit détaillé si besoin
    st.session_state.stocks = charger_etat_global("stocks", stocks_defaut)

# Notes
if "notes" not in st.session_state:
    st.session_state.notes = charger_etat_global("notes", [])

# CA du jour (simple compteur local + sauvegarde globale)
if "ca_jour" not in st.session_state:
    st.session_state.ca_jour = charger_etat_global("ca_jour", 0.0)

# Réservations (structure mémoire pour certaines fonctions locales)
if "reservations" not in st.session_state:
    st.session_state.reservations = {}

if "groupe_selectionne" not in st.session_state:
    st.session_state.groupe_selectionne = None

# =========================================================
# 6. NAVIGATION LATÉRALE
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

# Chargement des réservations du jour (Supabase)
resas_du_jour = charger_reservations(date_travail)

# =========================================================
# 7. MODULE : PLAN DE LA PLAGE
# =========================================================
if page == "🏖️ Plan de la plage":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
    st.write("")

    # Injection automatique des réservations du jour sur les places libres
    for resa in resas_du_jour:
        place = resa.get("emplacement")
        if not place:
            continue
        # on autorise un seul emplacement simple (ex: 'L1-G3' ou '1-3' → on normalise)
        if "-" in place and not place.startswith("L"):
            # format '1-3' → on convertit en 'L1-G3'
            l, g = place.split("-")
            place_norm = f"L{l}-G{g}"
        else:
            place_norm = place

        if place_norm in st.session_state.plage and st.session_state.plage[place_norm].get("statut", "Libre") == "Libre":
            st.session_state.plage[place_norm].update({
                "statut": "Occupé",
                "client": resa["client"],
                "nb_transats": resa.get("transats", 2),
                "heure_arrivee": resa.get("heure_arrivee", "09:00"),
                "transats_payes": resa.get("transats_payes", False),
                "prix_transats_encaisse": 0.0,
                "conso_ardoise": resa.get("conso_ardoise", 0.0),
                "historique_conso": resa.get("historique_conso", []),
                "paye_direct": resa.get("paye_direct", 0.0),
                "historique_paye_direct": []
            })

    for l in range(1, 8):
        st.caption(f"Ligne {l}")
        cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])

        # Groupes 1 à 5
        for g in range(1, 6):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut", "Libre") == "Libre" else f"🔴\n{info.get('client', 'Occupé')}"
            if cols[g-1].button(label, key=id_c, type="secondary" if info.get("statut", "Libre") == "Libre" else "primary"):
                st.session_state.groupe_selectionne = id_c
                st.rerun()

        with cols[5]:
            st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

        # Groupes 6 à 10
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
            # Sécurisation des clés
            for k, v in {
                "historique_conso": [],
                "historique_paye_direct": [],
                "paye_direct": 0.0,
                "conso_ardoise": 0.0
            }.items():
                if k not in st.session_state.plage[id_sel]:
                    st.session_state.plage[id_sel][k] = v

            info = st.session_state.plage[id_sel]
            num_l, num_g = id_sel.replace("L", "").split("-G")
            st.markdown(f"#### Emplacement **{num_l}-{num_g}**")

            # Cas libre → installation
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
                        # on crée aussi une réservation "passage" dans Supabase
                        nouvelle_resa = {
                            "client": nom.strip(), "telephone": "Passage", "transats": int(nb_t),
                            "preference": "", "emplacement": f"{num_l}-{num_g}", "est_place": True,
                            "date_resa": str(date_travail), "statut": "Occupé",
                            "heure_arrivee": h_a, "heure_depart": "", "montant": 0.0,
                            "transats_payes": False, "conso_ardoise": 0.0, "paye_direct": 0.0,
                            "historique_conso": []
                        }
                        sauvegarder_reservation(nouvelle_resa)
                        sauvegarder_etat_global("plage", st.session_state.plage)
                        st.session_state.groupe_selectionne = None
                        st.rerun()
                    else:
                        st.error("Nom obligatoire.")

            # Cas occupé → gestion complète
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
                        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                        sauvegarder_etat_global("plage", st.session_state.plage)
                        st.rerun()
                else:
                    st.success(f"✅ Transats réglés en direct ({info.get('prix_transats_encaisse', 0.0):.2f} €)")

                st.write("---")
                st.write("🛒 **Ajouter une Consommation :**")
                produit_choisi = st.selectbox("Choisir l'article :", list(TARIFS_CONSO.keys()))
                prix_unitaire = TARIFS_CONSO[produit_choisi]
                st.info(f"Prix unitaire : {prix_unitaire:.2f} €")

                col_btn_ard, col_btn_dir = st.columns(2)
                with col_btn_ard:
                    if st.button("➕ Ajouter à l'Ardoise", key=f"btn_ard_{id_sel}", use_container_width=True):
                        st.session_state.plage[id_sel]["conso_ardoise"] += prix_unitaire
                        st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                        # décrémentation stock si produit géré
                        if produit_choisi in st.session_state.stocks:
                            st.session_state.stocks[produit_choisi] = max(0, st.session_state.stocks[produit_choisi] - 1)
                        sauvegarder_etat_global("plage", st.session_state.plage)
                        sauvegarder_etat_global("stocks", st.session_state.stocks)
                        st.rerun()

                with col_btn_dir:
                    if st.button("⚡ Encaisser Direct", key=f"btn_dir_{id_sel}", use_container_width=True, type="primary"):
                        st.session_state.ca_jour += prix_unitaire
                        st.session_state.plage[id_sel]["paye_direct"] += prix_unitaire
                        st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                        if produit_choisi in st.session_state.stocks:
                            st.session_state.stocks[produit_choisi] = max(0, st.session_state.stocks[produit_choisi] - 1)
                        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                        sauvegarder_etat_global("plage", st.session_state.plage)
                        sauvegarder_etat_global("stocks", st.session_state.stocks)
                        st.rerun()

                if info.get("historique_conso") or info.get("historique_paye_direct"):
                    with st.expander("👀 Voir le détail des consos"):
                        if info.get("historique_conso"):
                            st.write("**Sur l'Ardoise :**")
                            for c in info["historique_conso"]:
                                st.text(f" ⏳ {c}")
                        if info.get("historique_paye_direct"):
                            st.write("**Déjà payé en direct :**")
                            for c in info["historique_paye_direct"]:
                                st.text(f" ✅ {c}")

                st.write("---")
                transats_dus = 0.0 if info.get("transats_payes", False) else frais_transats
                total_du_final = transats_dus + info.get("conso_ardoise", 0.0)

                st.markdown(
                    f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ EN DIRECT : "
                    f"{info.get('paye_direct', 0.0) + info.get('prix_transats_encaisse', 0.0):.2f} €</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='total-display'>RESTE À PAYER AU DÉPART : {total_du_final:.2f} €</div>",
                    unsafe_allow_html=True
                )

                col_f1, col_f2 = st.columns(2)
                if col_f1.button("💵 ENCAISSER RESTE & LIBÉRER", type="primary"):
                    st.session_state.ca_jour += total_du_final
                    st.session_state.plage[id_sel] = {
                        "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
                        "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                        "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                    }
                    sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                    sauvegarder_etat_global("plage", st.session_state.plage)
                    st.session_state.groupe_selectionne = None
                    st.rerun()
                if col_f2.button("Fermer"):
                    st.session_state.groupe_selectionne = None
                    st.rerun()

        gerer_place(st.session_state.groupe_selectionne)

# =========================================================
# 8. MODULE : PÉDALOS
# =========================================================
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
                                "statut": "En Mer", "client": nom_p, "heure_depart": h_dep_p,
                                "duree_prevue": duree_p, "total_du": prix_p
                            })
                            sauvegarder_etat_global("pedalos", st.session_state.pedalos)
                            st.rerun()
                        else:
                            st.error("Entrez un nom")
                else:
                    if st.button("💵 Retour & Encaisser", key=f"btn_r_{p_id}", type="primary", use_container_width=True):
                        st.session_state.ca_jour += p_info["total_du"]
                        st.session_state.pedalos[p_id].update({
                            "statut": "Disponible", "client": "", "heure_depart": "",
                            "duree_prevue": "1h", "total_du": 0.0
                        })
                        sauvegarder_etat_global("ca_jour", st.session_state.ca_jour)
                        sauvegarder_etat_global("pedalos", st.session_state.pedalos)
                        st.rerun()

# =========================================================
# 9. MODULE : NOTES
# =========================================================
elif page == "📝 Notes (To-Do List)":
    st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
    col_note, col_btn = st.columns([4, 1])
    nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Nettoyer la ligne 3")
    if col_btn.button("Ajouter"):
        if nouvelle_note:
            st.session_state.notes.append(nouvelle_note)
            sauvegarder_etat_global("notes", st.session_state.notes)
            st.rerun()
    st.write("---")
    notes_a_supprimer = []
    for i, note in enumerate(st.session_state.notes):
        if st.checkbox(note, key=f"note_{i}"):
            notes_a_supprimer.append(i)
    if notes_a_supprimer:
        for i in reversed(notes_a_supprimer):
            st.session_state.notes.pop(i)
        sauvegarder_etat_global("notes", st.session_state.notes)
        st.rerun()

# =========================================================
# 10. MODULE : STOCKS
# =========================================================
elif page == "📦 Stocks & Frigos":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📦 GESTION DES STOCKS & FRIGOS</h3>", unsafe_allow_html=True)
    st.write("---")

    st.info("💡 Cet onglet sert uniquement à enregistrer les livraisons (Réassort). Les stocks diminuent automatiquement à chaque vente sur le plan de la plage.")

    col_h1, col_h2, col_h3 = st.columns([3, 1.5, 2])
    with col_h1:
        st.markdown("**Produit**")
    with col_h2:
        st.markdown("**Quantité en réserve**")
    with col_h3:
        st.markdown("**Ajouter du stock (Réassort)**")
    st.write("---")

    # On boucle sur tous les produits connus (TARIFS_CONSO + clés existantes)
    tous_produits = set(TARIFS_CONSO.keys()) | set(st.session_state.stocks.keys())
    for produit in sorted(tous_produits):
        if produit not in st.session_state.stocks:
            st.session_state.stocks[produit] = 0

        quantite_actuelle = st.session_state.stocks[produit]

        col_nom, col_qte, col_actions = st.columns([3, 1.5, 2])
        with col_nom:
            st.write(f"🍹 {produit}")
        with col_qte:
            if quantite_actuelle <= 5:
                st.markdown(f"<b style='color: #dc2626;'>{quantite_actuelle} ⚠️ (Bas)</b>", unsafe_allow_html=True)
            else:
                st.markdown(f"<b style='color: #16a34a;'>{quantite_actuelle}</b>", unsafe_allow_html=True)
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
# 11. MODULE : CHIFFRE D'AFFAIRES
# =========================================================
elif page == "📊 Chiffre d'Affaires":
    st.markdown("<h3 style='color: #854d0e;'>📊 Caisse du Jour</h3>", unsafe_allow_html=True)
    st.metric("Total Encaissé Aujourd'hui", f"{st.session_state.ca_jour:.2f} €")

# =========================================================
# 12. MODULE : RÉSERVATIONS
# =========================================================
elif page == "📅 Réservations":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📅 GESTION & PRÉPARATION DES RÉSERVATIONS</h3>", unsafe_allow_html=True)
    st.write("---")

    # Formulaire d'ajout de réservation
    with st.form("form_nouvelle_resa"):
        st.markdown("##### ➕ Insérer une réservation planifiée")
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
                # on utilise le calcul tarifaire simple
                montant, _, _ = calculer_tarif_heures(h_ar, h_de, nb_tr)
                nouvelle_resa = {
                    "client": nom_c.strip(), "telephone": tel_c.strip(), "transats": int(nb_tr),
                    "preference": pref.strip(), "emplacement": "", "est_place": False,
                    "date_resa": str(date_travail), "statut": "Confirmé",
                    "heure_arrivee": h_ar, "heure_depart": h_de, "montant": montant,
                    "transats_payes": False, "conso_ardoise": 0.0, "paye_direct": 0.0,
                    "historique_conso": []
                }
                sauvegarder_reservation(nouvelle_resa)
                st.success(f"Réservation enregistrée pour {nom_c} ({montant:.2f} € calculés).")
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
            st.markdown(
                f"• **{r['client']}** — {r['transats']} Transat(s) — "
                f"Horaires : {r['heure_arrivee']} à {r['heure_depart']} | "
                f"**Statut :** `{statut_visuel}`"
            )
