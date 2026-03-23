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

# --- 3. L'OEIL DE L'AGENT (Lecture Web Optimisée) ---
def lire_site_web(url):
    """Utilise le moteur Jina Reader pour 'voir' le site comme un humain."""
    try:
        # On utilise le proxy Reader qui est gratuit et ultra-puissant
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=15)
        if response.status_code == 200:
            return response.text[:15000] # On prend les 15k premiers caractères (très riche)
        else:
            return "Erreur de lecture du site."
    except Exception as e:
        return f"Erreur technique de connexion : {e}"

# --- 4. LE CERVEAU DE L'AGENT ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 1. L'IA 'regarde' le site
    st.info(f"🕶️ L'agent examine le site : {target}...")
    vision_du_site = lire_site_web(target)

    # 2. Récupération historique
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n[RAPPEL DE TA DERNIÈRE ANALYSE] : {latest['report_text'][:1000]}"

    # 3. Le Prompt de Senior Strategist
    prompt_instruction = f"""Tu es mon Agent Senior en Intelligence Stratégique. 
    Tu viens de scanner le site {target}. Voici ce que tu as 'vu' (le contenu brut) :
    
    --- DEBUT DU SCAN ---
    {vision_du_site}
    --- FIN DU SCAN ---
    
    {comp_context}

    MISSION : Produis un rapport de veille concurrentielle "Sincérité Radicale". 
    Ne fais pas de remplissage. Si tu vois un changement de prix ou un nouveau produit, note-le.
    
    STRUCTURE DU RAPPORT :
    1. 🔴 CHANGEMENTS MAJEURS : Ce qui a bougé depuis la dernière fois (ou les 3 points clés).
    2. 💰 ANALYSE PRIX & OFFRE : Gammes détectées, promos en cours.
    3. 🎨 DIRECTION ARTISTIQUE : Analyse visuelle du merchandising digital.
    4. 🔮 PRÉDICTION : Quelle est leur prochaine étape stratégique selon toi ?

    Ton ton doit être professionnel, tranchant et analytique."""

    try:
        # On utilise le modèle le plus récent et stable
        model = genai.GenerativeModel('gemini-2.0-flash-exp') 
        response = model.generate_content(prompt_instruction)
        return response.text
    except Exception as e:
        return f"L'IA a rencontré un problème : {e}"

# --- 5. INTERFACE SIDEBAR ---
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

# --- 6. INTERFACE PRINCIPALE ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer une veille stratégique")
    target_input = st.text_input("URL de la marque :", "https://www.5five.com/fr/")
    focus_input = st.selectbox("Focus :", ["Global", "Prix", "Design"])
    
    if st.button("Lancer l'Agent"):
        with st.spinner("L'agent analyse le site en temps réel..."):
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
    if st.button("🔄 Actualiser la veille"):
        with st.spinner("Scan du site en cours..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_report, 'focus': reports[0]['focus']
            })
            st.rerun()
    st.markdown("---")
    st.markdown(reports[0]['report_text'])
