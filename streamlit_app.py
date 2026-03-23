import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Agent Veille Stratégique Pro", page_icon="🕵️‍♂️", layout="wide")

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. L'OEIL DE L'AGENT (Lecture Web via Jina) ---
def lire_site_web(url):
    """Transforme le site web en texte structuré pour l'IA."""
    try:
        # On utilise Jina Reader pour 'voir' le site parfaitement
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=15)
        if response.status_code == 200:
            return response.text[:15000] # On donne assez de contexte à l'IA
        else:
            return "Erreur : Impossible d'accéder au contenu du site actuellement."
    except Exception as e:
        return f"Erreur de connexion : {e}"

# --- 4. LE CERVEAU DE L'AGENT ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 1. L'agent scanne le site
    st.info(f"🕶️ Scan stratégique de : {target}...")
    contenu_scan = lire_site_web(target)

    # 2. Contexte historique
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n[RAPPEL ANALYSE PRÉCÉDENTE] : {latest['report_text'][:1000]}"

    prompt = f"""Tu es un Agent Senior en Intelligence Stratégique.
    Voici le scan complet que tu viens de réaliser sur le site {target} :
    
    --- DONNÉES DU SCAN ---
    {contenu_scan}
    --- FIN DES DONNÉES ---
    
    {comp_context}

    MISSION : Produis un rapport d'analyse concurrentielle détaillé.
    CONSIGNE : Sois extrêmement précis sur les prix, les nouvelles gammes et les messages marketing visibles.
    
    FORMAT :
    1. 🔴 CHANGEMENTS MAJEURS (Highlights)
    2. 💰 OFFRE & PRIX (Analyse détaillée)
    3. 🎨 MERCHANDISING & IMAGE (Analyse du style)
    4. 🔮 PRÉDICTION STRATÉGIQUE (Next steps)"""

    try:
        # MISE À JOUR : On utilise le nom de modèle qui correspond à tes quotas disponibles
        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Problème d'analyse IA : {e}"

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🕵️‍♂️ Mes Veilles")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    st.markdown("---")
    unique_targets = sorted(list(set([ana['target_name'] for ana in db.all()])))
    for t_name in unique_targets:
        cols = st.columns([0.8, 0.2])
        if cols[0].button(f"🏢 {t_name}", key=f"t_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        if cols[1].button("🗑️", key=f"del_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer un Agent de Veille")
    target_input = st.text_input("URL de la marque :", "https://www.5five.com/fr/")
    focus_input = st.selectbox("Focus :", ["Global", "Prix", "Design"])
    
    if st.button("Lancer l'Analyse"):
        with st.spinner("L'agent explore le site..."):
            report = executer_analyse(target_input, focus_input)
            t_name = target_input.split("//")[-1].split("/")[0]
            db.insert({
                'id': str(uuid.uuid4()), 'target': target_input, 'target_name': t_name,
                'timestamp': datetime.now().timestamp(), 'report_text': report, 'focus': focus_input
            })
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    st.header(f"Rapport : {selected_target}")
    if st.button("🔄 Actualiser"):
        with st.spinner("Scan en cours..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_report, 'focus': reports[0]['focus']
            })
            st.rerun()
    st.markdown("---")
    st.markdown(reports[0]['report_text'])
