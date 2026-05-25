import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Chez Alex - Gestion Plage", page_icon="🏖️", layout="wide")

# --- STYLE SMARTPHONE & GROS BOUTONS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 55px;
        font-size: 16px !important;
        font-weight: bold;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    div[data-testid="stHorizontalBlock"] {
        background: #fdfdfd;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ : MOT DE PASSE GENERAL ---
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

if not st.session_state.authentifie:
    st.markdown("<h2 style='text-align: center;'>🔒 Accès Sécurisé - Chez Alex</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mdp_saisi = st.text_input("Mot de passe de la plage :", type="password")
        if st.button("Se connecter 🔓"):
            if mdp_saisi == st.secrets["password"]:
                st.session_state.authentifie = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect ❌")
else:
    # --- CONFIGURATION DES TARIFS ---
    TARIFS_TRANSATS = {"Journée": 15.0, "Demi-Journée (5h)": 12.0, "2 Heures": 7.0, "Abonné (Suivi)": 0.0}
    TARIFS_CONSO = {
        "Soda": 2.5, "Grande eau": 2.5, "Petite eau": 1.5, 
        "Café / Thé": 1.0, "Jus d'orange": 5.0, "Virgin mojito": 6.0, "Glace": 3.8
    }
    TARIFS_PEDALO = {"30 min": 15.0, "1h": 20.0}

    # --- INITIALISATION DE LA MEMOIRE DE L'APPLICATION ---
    if 'plage_data' not in st.session_state:
        st.session_state.plage_data = {}
    if 'pedalos' not in st.session_state:
        st.session_state.pedalos = []
    if 'historique_ventes' not in st.session_state:
        st.session_state.historique_ventes = []
    if "voir_tel" not in st.session_state:
        st.session_state.voir_tel = False

    # --- MENU PRINCIPAL TACTILE ---
    onglet = st.radio("Aller à :", ["🏖️ Plan des Transats", "🚣 Pédalos", "📊 Fin de journée (Archives)"], horizontal=True)
    st.divider()

    # ==========================================
    # ONGLET 1 : LE PLAN DES TRANSATS (MINI-GROUPES DE 2)
    # ==========================================
    if onglet == "🏖️ Plan des Transats":
        st.subheader("📋 Plan de la Plage (10 groupes de 2 transats par ligne)")
        
        if st.button("👁️ Afficher/Masquer les Téléphones (Sécurité)", type="secondary"):
            st.session_state.voir_tel = not st.session_state.voir_tel
            st.rerun()

        ligne_choisie = st.selectbox("Sélectionner la Ligne :", [f"Ligne {i}" for i in range(1, 8)])
        num_ligne = ligne_choisie.split()[1]

        st.write("### Cliquez sur un groupe de 2 transats :")
        
        # Partie Gauche : Groupes 1 à 5
        col_gauche = st.columns(5)
        for idx, col in enumerate(col_gauche, start=1):
            id_place = f"{num_ligne}-{idx}"
            occupe = id_place in st.session_state.plage_data
            label = f"🔴 Gp {idx}\n(Occupé)" if occupe else f"🟢 Gp {idx}\n(Libre)"
            if col.button(label, key=f"btn_{id_place}"):
                st.session_state.emplacement_actif = id_place

        # Allée centrale bien visible
        st.markdown("<div style='text-align:center; color:#ffaa00; font-weight:bold; padding:10px; background:#fff3cd; border-radius:8px; margin:15px 0;'>🚧 ALLÉE CENTRALE 🚧</div>", unsafe_allow_html=True)
        
        # Partie Droite : Groupes 6 à 10
        col_droite = st.columns(5)
        for idx, col in enumerate(col_droite, start=6):
            id_place = f"{num_ligne}-{idx}"
            occupe = id_place in st.session_state.plage_data
            label = f"🔴 Gp {idx}\n(Occupé)" if occupe else f"🟢 Gp {idx}\n(Libre)"
            if col.button(label, key=f"btn_{id_place}"):
                st.session_state.emplacement_actif = id_place

        # ACTION SUR LE GROUPE SÉLECTIONNÉ
        if "emplacement_actif" in st.session_state:
            id_p = st.session_state.emplacement_actif
            st.divider()
            st.markdown(f"### ⚙️ Gestion du **Groupe {id_p}** (2 transats)")
            
            # Formulaire d'installation
            if id_p not in st.session_state.plage_data:
                with st.form(f"install_{id_p}"):
                    nom = st.text_input("Nom du client :")
                    tel = st.text_input("Téléphone :")
                    forfait = st.selectbox("Tarif Transat (par transat) :", list(TARIFS_TRANSATS.keys()))
                    nb_transats = st.slider("Nombre de transats utilisés dans ce groupe :", 1, 2, 2)
                    notes = st.text_input("Notes particulières :")
                    
                    if st.form_submit_button("✅ Installer le client"):
                        st.session_state.plage_data[id_p] = {
                            "nom": nom, "tel": tel, "forfait": forfait, "nb_transats": nb_transats,
                            "notes": notes, "conso": [], "heure_arrivee": datetime.now().strftime("%H:%M")
                        }
                        st.success("Client installé !")
                        st.rerun()
            else:
                # Gestion des consommations et encaissement
                client = st.session_state.plage_data[id_p]
                tel_aff = client['tel'] if st.session_state.voir_tel else "•• •• •• ••"
                
                st.write(f"👤 **Client :** {client['nom']} | 📞 **Tel :** {tel_aff} | ⏰ **Arrivé à :** {client['heure_arrivee']}")
                st.write(f"🏖️ Forfait : {client['forfait']} ({client['nb_transats']} transat(s) occupé(s))")
                
                # Calcul de l'addition
                prix_ombrage = TARIFS_TRANSATS[client['forfait']] * client['nb_transats']
                prix_boissons = sum([TARIFS_CONSO[c] for c in client['conso']])
                total_global = prix_ombrage + prix_boissons
                
                st.markdown(f"## 💰 Total à payer : {total_global:.2f} €")
                
                # Boutons de consommations rapides
                st.write("➕ **Ajouter une boisson/glace sur la note :**")
                c_boites = st.columns(4)
                for i, item in enumerate(TARIFS_CONSO.keys()):
                    if c_boites[i % 4].button(f"{item}\n({TARIFS_CONSO[item]}€)"):
                        st.session_state.plage_data[id_p]['conso'].append(item)
                        st.success(f"Ajouté : 1 {item}")
                        st.rerun()
                
                if client['conso']:
                    st.write(f"🛒 **Consos actuelles :** {', '.join(client['conso'])}")
                
                st.write("---")
                # Bouton d'encaissement (Envoie la ligne dans l'historique de la journée)
                if st.button("💵 CLIENT PAYE & S'EN VA (Enregistrer la vente)", type="primary"):
                    # On crée la ligne d'archive
                    vente = {
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Type": "Transat",
                        "Emplacement": f"Groupe {id_p}",
                        "Nom Client": client['nom'],
                        "Telephone": client['tel'],
                        "Détails": f"{client['forfait']} ({client['nb_transats']} transats)",
                        "Consos": ", ".join(client['conso']) if client['conso'] else "Aucune",
                        "Total Payé (€)": total_global
                    }
                    st.session_state.historique_ventes.append(vente)
                    st.session_state.plage_data.pop(id_p) # Libère la place
                    st.success("Vente archivée ! L'emplacement est de nouveau libre.")
                    st.rerun()

    # ==========================================
    # ONGLET 2 : LA PAGE PÉDALOS
    # ==========================================
    elif onglet == "🚣 Pédalos":
        st.subheader("🚣 Location des Pédalos")
        with st.form("pedalo_form"):
            p_nom = st.text_input("Nom du client :")
            p_duree = st.selectbox("Durée :", list(TARIFS_PEDALO.keys()))
            if st.form_submit_button("🚀 Lancer le pédalo"):
                st.session_state.pedalos.append({
                    "nom": p_nom, "duree": p_duree, "prix": TARIFS_PEDALO[p_duree], "statut": "En mer"
                })
                st.rerun()
        
        st.write("### ⏱️ Pédalos actuellement sortis :")
        for idx, p in enumerate(st.session_state.pedalos):
            if p['statut'] == "En mer":
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    st.write(f"🚣 **{p['nom']}** - Forfait {p['duree']} ({p['prix']} €)")
                with col_p2:
                    if st.button("💵 Encaisser Retour", key=f"p_{idx}"):
                        vente_p = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Type": "Pédalo",
                            "Emplacement": "Mer",
                            "Nom Client": p['nom'],
                            "Telephone": "-",
                            "Détails": f"Pédalo {p['duree']}",
                            "Consos": "-",
                            "Total Payé (€)": p['prix']
                        }
                        st.session_state.historique_ventes.append(vente_p)
                        st.session_state.pedalos[idx]['statut'] = "Retourné"
                        st.success("Pédalo encaissé et archivé !")
                        st.rerun()

    # ==========================================
    # ONGLET 3 : FIN DE JOURNÉE & TELECHARGEMENT ARCHIVES
    # ==========================================
    elif onglet == "📊 Fin de journée (Archives)":
        st.subheader("📊 Récapitulatif et Téléchargement des archives")
        
        if not st.session_state.historique_ventes:
            st.info("Aucune vente enregistrée pour le moment aujourd'hui.")
        else:
            df_ventes = pd.DataFrame(st.session_state.historique_ventes)
            
            # Calcul du Chiffre d'Affaire de la journée
            ca_total = df_ventes["Total Payé (€)"].sum()
            st.metric(label="💰 Chiffre d'Affaires Total Encaissé", value=f"{ca_total:.2f} €")
            
            st.write("### 📋 Liste de toutes les ventes du jour :")
            st.dataframe(df_ventes, use_container_width=True)
            
            st.write("---")
            st.markdown("### 📥 ÉTAPE DE SÉCURITÉ POUR LA PATRONNE :")
            st.write("Avant de fermer le site ce soir, cliquez sur le bouton ci-dessous pour télécharger le fichier Excel de la journée sur votre téléphone :")
            
            # Transformation en fichier Excel/CSV téléchargeable d'un clic
            csv = df_ventes.to_csv(index=False).encode('utf-8')
            nom_fichier = f"archives_plage_{datetime.now().strftime('%Y-%m-%d')}.csv"
            
            st.download_button(
                label="💾 TÉLÉCHARGER LE BILAN DU JOUR (Excel/CSV)",
                data=csv,
                file_name=nom_fichier,
                mime='text/csv',
                type="primary"
            )
