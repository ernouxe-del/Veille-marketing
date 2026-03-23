import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid
import requests
from bs4 import BeautifulSoup

# --- 1. CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

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

# --- 3. FONCTION DE LECTURE DU SITE (SCRAPING) ---
def extraire_texte_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # On nettoie le code pour ne garder que le texte
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
            
        texte = soup.get_text(separator=' ')
        lignes = (line.strip() for line in texte.splitlines())
        chunks = (phrase.strip() for line in lignes for phrase in line.split("  "))
        texte_propre = '\n'.join(chunk for chunk in chunks if chunk)
        
        return texte_propre[:10000] # Limite pour l'IA
    except Exception as e:
        return f"Note : Impossible de lire le contenu en direct ({e})."

# --- 4. LE CERVEAU DE L'AGENT ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Lecture du contenu du site
    contenu_site = extraire_texte_url(target) if "http" in target else "Analyse basée sur tes connaissances."

    # Historique pour comparaison
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\n[HISTORIQUE PRÉCÉDENT POUR COMPARAISON] : {latest_past['report_text'][:1000]}"

    instructions = f"""Tu es un Agent Senior en Intelligence Stratégique.
    Voici des données extraites récemment de la cible {target} :
    ---
    {contenu_site}
    ---
    {comp_context}

    TA MISSION : Rédiger un rapport de veille stratégique précis.
    FORMAT :
    1. 📌 HIGHLIGHTS : 3 points majeurs.
    2. 💻 STOREFRONT : Analyse de l'offre et du merchandising.
    3. 🏆 MAPPING : Produits phares et prix.
    4. 🔮 PRÉDICTION : Évolution stratégique à venir.
    
    IMPORTANT : Sois factuel. Cite des éléments du texte si possible."""

    try:
        # MISE À JOUR : Utilisation du modèle Gemini 2.5 Flash qui est actif sur ton compte
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instructions)
        prompt = f"Effectue l'analyse de {target}. Focus : {focus}."
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🕵️‍♂️ Mes Veilles")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    st.markdown("---")
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

# --- 6. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Nouvelle Analyse Stratégique")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL ou Marque :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Analyse en cours..."):
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
    st.header(f"Veille : {selected_target}")
    
    if st.button("🔄 Actualiser"):
        with st.spinner("Mise à jour..."):
            new_text = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_text, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.markdown(reports[0]['report_text'])
