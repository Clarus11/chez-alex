# app.py
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
import traceback

# ==========================================
# 0. SECRETS SUPABASE
# ==========================================
# Assure-toi d'avoir défini SUPABASE_URL et SUPABASE_KEY dans les secrets Streamlit
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "SUPABASE_URL_EXEMPLE")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "SUPABASE_KEY_EXEMPLE")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Date du jour (format ISO pour la base)
aujourd_hui = str(date.today())

# ==========================================
# 1. CONFIG PAGE
# ==========================================
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

# ==========================================
# 2. UTILITAIRES
# ==========================================
def safe_print_exception(prefix="Erreur"):
    st.error(f"{prefix} — voir console pour trace complète.")
    print(prefix)
    traceback.print_exc()

def calculer_tarif_heures(heure_arr, heure_dep, nb_transats):
    """
    Corrigé : on utilise datetime.strptime (importé plus haut).
    Retourne (montant_total, heures, libelle)
    """
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
    except Exception as e:
        # Affiche l'erreur pour debug
        st.error(f"Erreur calcul tarif: {e}")
        print("Trace calcul_tarif_heures:")
        traceback.print_exc()
        return 15.0 * nb_transats, 0.0, "Tarif Journée (Défaut)"

# ==========================================
# 3. AUTHENTIFICATION SIMPLE
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
                st.experimental_rerun()
            else:
                st.error("Mot de passe incorrect ❌")
    st.stop()

# Debug pour confirmer qu'on passe l'auth
st.write("DEBUG Le code est bien arrivé ici après authentification")

# ==========================================
# 4. INITIALISATION DES STRUCTURES EN SESSION
# ==========================================
# Initialisation minimale avant tout accès
if "plage" not in st.session_state:
    st.session_state.plage = {}

# Crée la grille L1-G1 à L7-G10 si nécessaire
if not st.session_state.plage:
    for l in range(1, 8):
        for g in range(1, 11):
            id_c = f"L{l}-G{g}"
            st.session_state.plage[id_c] = {
                "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
                "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
            }

# Autres structures
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

# ==========================================
# 5. FONCTION DE CHARGEMENT DE SUPABASE
# ==========================================
def charger_donnees_depuis_supabase():
    """
    Doit uniquement lire Supabase et mettre à jour st.session_state.plage.
    Ne recrée pas la structure complète.
    """
    try:
        rep = supabase.table("transats").select("*").eq("date", aujourd_hui).execute()
        # rep.data peut être None ou liste
        rows = rep.data or []
        for ligne in rows:
            id_c = ligne.get("numero_transat")
            if not id_c:
                continue
            # Si la place n'existe pas dans la grille, on l'ignore
            if id_c not in st.session_state.plage:
                continue
            st.session_state.plage[id_c]["statut"] = ligne.get("statut_paiement", "Occupé")
            st.session_state.plage[id_c]["client"] = ligne.get("nom_client", "")
            try:
                st.session_state.plage[id_c]["prix_transats_encaisse"] = float(ligne.get("prix", 0.0))
            except:
                st.session_state.plage[id_c]["prix_transats_encaisse"] = 0.0
    except Exception as e:
        safe_print_exception("Erreur chargement transats depuis Supabase")

# Charger une seule fois par session
if "donnees_chargees" not in st.session_state:
    charger_donnees_depuis_supabase()
    st.session_state.donnees_chargees = True

# ==========================================
# 6. SIDEBAR NAVIGATION
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
        st.experimental_rerun()

# ==========================================
# 7. MODULES PRINCIPAUX
# ==========================================
if page == "🏖️ Plan de la plage":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>PLAN DU JOUR</h3>", unsafe_allow_html=True)
    date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
    resas_du_jour = st.session_state.reservations.get(date_aujourdhui, [])

    # Injecte réservations si place libre
    for resa in resas_du_jour:
        place = resa.get("emplacement")
        if place and place in st.session_state.plage and st.session_state.plage[place].get("statut", "Libre") == "Libre":
            st.session_state.plage[place].update({
                "statut": "Occupé",
                "client": resa.get("client", ""),
                "nb_transats": resa.get("transats", 2),
                "heure_arrivee": "09:00",
                "transats_payes": False,
                "prix_transats_encaisse": 0.0,
                "conso_ardoise": 0.0,
                "historique_conso": [],
                "paye_direct": 0.0,
                "historique_paye_direct": []
            })

    # Affichage grille
    for l in range(1, 8):
        st.caption(f"Ligne {l}")
        cols = st.columns([1, 1, 1, 1, 1, 0.4, 1, 1, 1, 1, 1])
        # colonnes 1..5
        for g in range(1, 6):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut", "Libre") == "Libre" else f"🔴\n{info.get('client', 'Occupé')}"
            if cols[g-1].button(label, key=f"btn_place_{id_c}"):
                st.session_state.groupe_selectionne = id_c
                st.experimental_rerun()

        with cols[5]:
            st.markdown("<div class='allee-verticale'>ALLÉE</div>", unsafe_allow_html=True)

        # colonnes 6..10
        for g in range(6, 11):
            id_c = f"L{l}-G{g}"
            info = st.session_state.plage[id_c]
            label = f"🟢\n{l}-{g}" if info.get("statut", "Libre") == "Libre" else f"🔴\n{info.get('client', 'Occupé')}"
            if cols[g].button(label, key=f"btn_place_{id_c}_r"):
                st.session_state.groupe_selectionne = id_c
                st.experimental_rerun()

    # Gestion de la place sélectionnée via modal
    if st.session_state.groupe_selectionne:
        id_sel = st.session_state.groupe_selectionne
        info = st.session_state.plage[id_sel]

        # Réparations de sécurité
        if "historique_conso" not in info:
            info["historique_conso"] = []
        if "historique_paye_direct" not in info:
            info["historique_paye_direct"] = []
        if "paye_direct" not in info:
            info["paye_direct"] = 0.0
        if "conso_ardoise" not in info:
            info["conso_ardoise"] = 0.0

        num_l, num_g = id_sel.replace("L", "").split("-G")
        st.markdown(f"#### Emplacement **{num_l}-{num_g}**")

        if info["statut"] == "Libre":
            nom = st.text_input("👤 Nom du client :", key=f"nom_client_{id_sel}")
            nb_t = st.number_input("🪑 Nombre de transats :", min_value=1, max_value=4, value=2, key=f"nbt_{id_sel}")
            h_a = st.text_input("⏰ Heure d'arrivée :", datetime.now().strftime("%H:%M"), key=f"ha_{id_sel}")

            if st.button("✅ Installer le client", key=f"installer_{id_sel}"):
                if nom:
                    st.session_state.plage[id_sel].update({
                        "statut": "Occupé", "client": nom, "nb_transats": nb_t, "heure_arrivee": h_a,
                        "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                        "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                    })
                    # Sauvegarde Supabase
                    try:
                        nouvelle_resa = {
                            "date": aujourd_hui,
                            "numero_transat": id_sel,
                            "nom_client": nom,
                            "periode": "Journée",
                            "prix": 0.0,
                            "statut_paiement": "Occupé"
                        }
                        supabase.table("transats").insert(nouvelle_resa).execute()
                    except Exception as e:
                        safe_print_exception("Erreur sauvegarde installation")
                    st.session_state.groupe_selectionne = None
                    st.experimental_rerun()
                else:
                    st.error("Nom obligatoire.")
        else:
            st.markdown(f"👤 **{info['client']}** | 🪑 {info['nb_transats']} transats | ⏰ Arrivée : {info['heure_arrivee']}")
            h_actuelle = datetime.now().strftime("%H:%M")
            h_dep = st.text_input("⏳ Heure de départ / calcul :", h_actuelle, key=f"hd_{id_sel}")

            frais_transats, heures_passees, libelle_tarif = calculer_tarif_heures(info["heure_arrivee"], h_dep, info["nb_transats"])
            st.markdown(f"⏱️ *Temps : {heures_passees:.2f}h* — **{libelle_tarif}**")

            st.write("---")
            st.write("💰 **Règlement des Transats :**")
            if not info.get("transats_payes", False):
                st.warning(f"Montant dû : {frais_transats:.2f} €")
                if st.button("💵 Encaisser les transats DIRECT (Sur le transat)", key=f"encaisser_transat_{id_sel}"):
                    st.session_state.ca_jour += frais_transats
                    st.session_state.plage[id_sel]["transats_payes"] = True
                    st.session_state.plage[id_sel]["prix_transats_encaisse"] = frais_transats
                    try:
                        supabase.table("transats").update({
                            "prix": frais_transats,
                            "statut_paiement": "Payé"
                        }).eq("date", aujourd_hui).eq("numero_transat", id_sel).execute()
                    except Exception as e:
                        safe_print_exception("Erreur mise à jour paiement transat")
                    st.experimental_rerun()
            else:
                st.success(f"✅ Transats réglés en direct ({info.get('prix_transats_encaisse', 0.0):.2f} €)")

            st.write("---")
            st.write("🛒 **Ajouter une Consommation :**")
            produit_choisi = st.selectbox("Choisir l'article :", list(TARIFS_CONSO.keys()), key=f"sel_prod_{id_sel}")
            prix_unitaire = TARIFS_CONSO[produit_choisi]
            st.info(f"Prix unitaire : {prix_unitaire:.2f} €")

            col_btn_ard, col_btn_dir = st.columns(2)
            with col_btn_ard:
                if st.button("➕ Ajouter à l'Ardoise", key=f"btn_ard_{id_sel}"):
                    try:
                        st.session_state.plage[id_sel]["conso_ardoise"] += prix_unitaire
                        st.session_state.plage[id_sel]["historique_conso"].append(f"{produit_choisi} (Ardoise)")
                        st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi, 0) - 1
                        nouvelle_conso = {
                            "article": produit_choisi,
                            "quantite": 1,
                            "prix_total": prix_unitaire,
                            "numero_transat_associe": id_sel
                        }
                        supabase.table("consommations").insert(nouvelle_conso).execute()
                    except Exception as e:
                        safe_print_exception("Erreur ajout ardoise")
                    st.experimental_rerun()

            with col_btn_dir:
                if st.button("⚡ Encaisser Direct", key=f"btn_dir_{id_sel}"):
                    try:
                        st.session_state.ca_jour += prix_unitaire
                        st.session_state.plage[id_sel]["paye_direct"] += prix_unitaire
                        st.session_state.plage[id_sel]["historique_paye_direct"].append(f"{produit_choisi} (Direct)")
                        st.session_state.stocks[produit_choisi] = st.session_state.stocks.get(produit_choisi, 0) - 1
                        nouvelle_conso = {
                            "article": produit_choisi,
                            "quantite": 1,
                            "prix_total": prix_unitaire
                        }
                        supabase.table("consommations").insert(nouvelle_conso).execute()
                    except Exception as e:
                        safe_print_exception("Erreur encaissement direct")
                    st.experimental_rerun()

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

            st.markdown(f"<div class='paye-direct-display'>DÉJÀ ENCAISSÉ EN DIRECT : {info.get('paye_direct', 0.0) + info.get('prix_transats_encaisse', 0.0):.2f} €</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='total-display'>RESTE À PAYER AU DÉPART : {total_du_final:.2f} €</div>", unsafe_allow_html=True)

            col_f1, col_f2 = st.columns(2)
            if col_f1.button("💵 ENCAISSER RESTE & LIBÉRER", key=f"liberer_{id_sel}"):
                try:
                    st.session_state.ca_jour += total_du_final
                    supabase.table("transats").update({
                        "prix": info.get('prix_transats_encaisse', 0.0) + transats_dus,
                        "statut_paiement": "Libre"
                    }).eq("date", aujourd_hui).eq("numero_transat", id_sel).execute()
                except Exception as e:
                    safe_print_exception("Erreur clôture transat")
                st.session_state.plage[id_sel] = {
                    "statut": "Libre", "client": "", "heure_arrivee": "", "nb_transats": 2,
                    "transats_payes": False, "prix_transats_encaisse": 0.0, "conso_ardoise": 0.0,
                    "historique_conso": [], "paye_direct": 0.0, "historique_paye_direct": []
                }
                st.session_state.groupe_selectionne = None
                st.experimental_rerun()

            if col_f2.button("Fermer", key=f"fermer_{id_sel}"):
                st.session_state.groupe_selectionne = None
                st.experimental_rerun()

# Pédalos
elif page == "🛶 Pédalos":
    st.markdown("<h3 style='text-align: center; color: #854d0e;'>🛶 GESTION DE LA FLOTTE DE PÉDALOS</h3>", unsafe_allow_html=True)
    st.write("Suivi des départs en mer et encaissement instantané.")
    st.write("---")
    for p_id, p_info in st.session_state.pedalos.items():
        with st.container():
            col_p1, col_p2, col_p3 = st.columns([2, 4, 3])
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
                    duree_p = st.radio("Durée demandée :", ["30 min (15€)", "1h (20€)"], key=f"dur_{p_id}", horizontal=True)
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
                                "statut": "En Mer", "client": nom_val, "heure_depart": h_dep_p, "duree_prevue": st.session_state.get(f"dur_{p_id}", "1h"), "total_du": prix_p
                            })
                            st.experimental_rerun()
                        else:
                            st.error("Entrez un nom")
                else:
                    if st.button("💵 Retour & Encaisser", key=f"btn_r_{p_id}", use_container_width=True):
                        st.session_state.ca_jour += p_info["total_du"]
                        st.session_state.pedalos[p_id].update({
                            "statut": "Disponible", "client": "", "heure_depart": "", "duree_prevue": "1h", "total_du": 0.0
                        })
                        st.experimental_rerun()

# Notes
elif page == "📝 Notes (To-Do List)":
    st.markdown("<h3 style='color: #854d0e;'>📝 Cahier de Liaison & Besoins</h3>", unsafe_allow_html=True)
    col_note, col_btn = st.columns([4, 1])
    nouvelle_note = col_note.text_input("Nouvelle tâche :", placeholder="Ex: Nettoyer la ligne 3")
    if col_btn.button("Ajouter"):
        if nouvelle_note:
            st.session_state.notes.append(nouvelle_note)
            st.experimental_rerun()
    st.write("---")
    notes_a_supprimer = []
    for i, note in enumerate(st.session_state.notes):
        if st.checkbox(note, key=f"note_{i}"):
            notes_a_supprimer.append(i)
    if notes_a_supprimer:
        for i in reversed(notes_a_supprimer):
            st.session_state.notes.pop(i)
        st.experimental_rerun()

# Stocks
elif page == "📦 Stocks & Frigos":
    st.markdown("<h3 style='color: #854d0e; text-align: center;'>📦 GESTION DES STOCKS & FRIGOS</h3>", unsafe_allow_html=True)
    st.write("---")
    st.info("💡 Cet onglet sert uniquement à enregistrer les livraisons (Réassort). Les stocks diminuent automatiquement à chaque vente sur le plan de la plage.")
    col_h1, col_h2, col_h3 = st.columns([3, 1.5, 2])
    with col_h1: st.markdown("**Produit**")
    with col_h2: st.markdown("**Quantité en réserve**")
    with col_h3: st.markdown("**Ajouter du stock (Réassort)**")
    st.write("---")
    for produit in TARIFS_CONSO.keys():
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
            if btn_col1.button("➕ 1", key=f"plus1_{produit}"):
                st.session_state.stocks[produit] += 1
                st.experimental_rerun()
            if btn_col2.button("➕ 10", key=f"plus10_{produit}"):
                st.session_state.stocks[produit] += 10
                st.experimental_rerun()

# Autres pages placeholders
else:
    st.write("Page en construction ou non implémentée.")
