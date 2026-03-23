import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

# CSS pour le look AI Studio
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1c22; }
    .stButton>button { width: 100%; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. SESSION STATE ---
if 'selected_analysis_id' not in st.session_state: st.session_state['selected_analysis_id'] = None

# --- 4. SIDEBAR (Historique) ---
with st.sidebar:
    st.title("🕵️‍♂️ Agent Veille")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_analysis_id'] = None
        st.rerun()
    st.markdown("---")
    all_analysis = sorted(db.all(), key=lambda x: x['timestamp'], reverse=True)
    for ana in all_analysis:
        date_str = datetime.fromtimestamp(ana['timestamp']).strftime("%d/%m")
        if st.button(f"📊 {ana['target_name']} ({date_str})", key=ana['id']):
            st.session_state['selected_analysis_id'] = ana['id']
            st.rerun()

# --- 5. CORPS PRINCIPAL ---
current_id = st.session_state['selected_analysis_id']

if current_id is None:
    st.header("Nouvelle Analyse Stratégique")
    col1, col2 = st.columns([1, 1])
    with col1:
        target = st.text_input("URL ou Marque :", "https://www.5five.com/fr/")
        focus = st.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Analyse approfondie du site et du marché..."):
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            # Recherche historique pour comparaison
            old_reports = db.search(Analysis.target == target)
            comp_context = ""
            if old_reports:
                latest = sorted(old_reports, key=lambda x: x['timestamp'], reverse=True)[0]
                comp_context = f"Dernière analyse : {latest['report_text'][:800]}"

            # --- INSTRUCTIONS MISES À JOUR (Focus Site Web & Merchandising) ---
            instructions = f"""Tu es un Expert en Intelligence Stratégique (Marché FR). 
            Analyse la cible de façon NEUTRE.
            
            STRUCTURE REQUISE :
            1. 📌 HIGHLIGHTS FR : 3 faits marquants du jour.
            
            2. 💻 DIGITAL STOREFRONT & MERCHANDISING : 
               - Analyse l'organisation du site (Home page, bannières).
               - Mise en avant par UNIVERS PRODUIT (ex: Cuisine, Rangement, Déco).
               - Note tout CHANGEMENT NOTABLE par rapport aux données précédentes.
               - Efficacité du tunnel de vente et promos visibles.
            
            3. 🏆 TOP 5 PRODUITS : Prix, Design, Stratégie.
            
            4. 🔄 ANALYSE COMPARATIVE : Différences clés détectées. {comp_context}
            
            5. 🎨 IDENTITÉ VISUELLE & 🔮 PRÉVISIONS.
            
            6. 🔗 SOURCES."""

            try:
                model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=instructions)
                response = model.generate_content(f"Analyse {target} au {datetime.now()}. Focus : {focus}")
                
                # Sauvegarde
                t_name = target.split("//")[-1].split("/")[0] if "http" in target else target
                db.insert({'id': str(uuid.uuid4()), 'target': target, 'target_name': t_name, 'timestamp': datetime.now().timestamp(), 'report_text': response.text, 'focus': focus})
                
                st.markdown(response.text)
                st.balloons()
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    ana = db.get(Analysis.id == current_id)
    st.header(f"Rapport : {ana['target_name']}")
    st.markdown(ana['report_text'])
    if st.button("⬅️ Retour"):
        st.session_state['selected_analysis_id'] = None
        st.rerun()
