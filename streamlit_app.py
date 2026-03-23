import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

st.markdown("""
<style>[data-testid="stSidebar"] { background-color: #1a1c22; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .date-badge { background-color: #343541; padding: 5px 10px; border-radius: 10px; font-size: 0.8rem; color: #ccc; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): 
    os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. LE CERVEAU DE L'AGENT ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Récupération de l'historique pour comparaison
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\n[HISTORIQUE PRÉCÉDENT POUR COMPARAISON] : {latest_past['report_text'][:1500]}"

    # Ton nouveau Prompt "AI Studio" optimisé
    instructions = f"""Tu es un Agent Senior en Intelligence Stratégique. Ton but est de détecter chaque changement subtil de stratégie.
    
    SOURCES DE VÉRITÉ : 
    Ta cible primaire est {target}. Tu dois explorer le site pour détecter les changements et les actualités indexées par Google Search.
    
    PILIERS D'ANALYSE (SINCÉRITÉ RADICALE) :
    1. Stratégie de Prix : Fluctuations, nouveaux schémas de remise, prix psychologiques.
    2. Catalogue Produit : Nouveautés ("New In") et articles abandonnés.
    3. Identité Visuelle (DA) : Style photo, palettes de couleurs, mise en page.
    4. Merchandising Digital : Analyse par UNIVERS (Cuisine, Rangement, Salle de bain, Mobilier, etc.).

    FORMAT DE RAPPORT OBLIGATOIRE :
    
    1. 📌 HIGHLIGHTS : Les 3 changements les plus importants (avec liens sources).
    
    2. 💻 DIGITAL STOREFRONT & UNIVERS :
       - Analyse de la Home Page (Hero Banner actuelle).
       - Organisation par Univers Produit.
       - Architecture de prix (Entrée de gamme, Milieu de gamme, Premium).
       - PREUVE (Lien URL) : [Lien exact]

    3. 🏆 MAPPING PRODUITS (Par catégorie) :
       Pour chaque produit phare détecté :
       - Nom du Produit & Gamme
       - Prix Actuel (min/max/moyenne)
       - Analyse Design (matériaux, couleurs, style)
       - Crochet Marketing (promesse visuelle)
       - PREUVE (Lien Fiche Produit) : [Lien direct obligatoire]

    4. 🔄 ANALYSE COMPARATIVE : {comp_context if comp_context else "Analyse des évolutions récentes."}
    
    5. 🔮 PRÉDICTION STRATÉGIQUE : Ce que cela signifie pour les 3 prochains mois.

    CONSTRAINTES STRICTES :
    - NE RIEN INVENTER : Si une info manque (ex: pas de Click & Collect ou de RSE visible), ne mentionne PAS ces sections.
    - Toujours citer les liens sources exacts sous chaque section."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instructions)
        prompt = f"Effectue un rapport de veille stratégique complet sur {target}. Focus : {focus}."
        
        # CHANGEMENT ICI : Le format dictionnaire exigé par la nouvelle version
        response = model.generate_content(
            prompt,
            tools=[{"google_search": {}}]
        )
        return response.text
        
    except Exception as e:
        return f"Erreur technique : {e}"

# --- 4. SIDEBAR (Gestion de l'historique) ---
with st.sidebar:
    st.title("🕵️‍♂️ Mes Veilles")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 Marques suivies")
    all_data = db.all()
    unique_targets = sorted(list(set([ana['target_name'] for ana in all_data])))
    
    for t_name in unique_targets:
        cols = st.columns([0.8, 0.2])
        if cols[0].button(f"🏢 {t_name}", key=f"target_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        if cols[1].button("🗑️", key=f"del_all_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

# --- 5. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Nouvelle Analyse Stratégique")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL ou Marque :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :",["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Analyse approfondie en cours..."):
            report_text = executer_analyse(target_input, focus_input)
            t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
            db.insert({
                'id': str(uuid.uuid4()), 'target': target_input, 'target_name': t_name,
                'timestamp': datetime.now().timestamp(), 'report_text': report_text, 'focus': focus_input
            })
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    col_t, col_up = st.columns([0.7, 0.3])
    col_t.header(f"Veille : {selected_target}")
    
    if col_up.button("🔄 Actualiser (Nouvelle version)"):
        with st.spinner("Mise à jour..."):
            new_text = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_text, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.subheader("📍 Dernière Analyse")
    st.markdown(reports[0]['report_text'])
    
    if len(reports) > 1:
        st.markdown("---")
        st.subheader("📜 Archives")
        for old_ana in reports[1:]:
            with st.expander(f"Version du {datetime.fromtimestamp(old_ana['timestamp']).strftime('%d/%m/%Y')}"):
                st.markdown(old_ana['report_text'])
