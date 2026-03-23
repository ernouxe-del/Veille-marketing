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
        
        # Supprimer les scripts et les styles inutiles
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
            
        texte = soup.get_text(separator=' ')
        # Nettoyage des espaces blancs en trop
        lignes = (line.strip() for line in texte.splitlines())
        chunks = (phrase.strip() for line in lignes for phrase in line.split("  "))
        texte_propre = '\n'.join(chunk for chunk in chunks if chunk)
        
        return texte_propre[:10000] # On limite à 10 000 caractères pour ne pas saturer l'IA
    except Exception as e:
        return f"Impossible de lire le site : {e}"

# --- 4. LE CERVEAU DE L'AGENT ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # ÉTAPE 1 : On va chercher le contenu du site nous-mêmes
    st.info(f"🔍 Lecture directe de {target}...")
    contenu_site = extraire_texte_url(target) if "http" in target else "Cible non-URL, analyse basée sur les connaissances internes."

    # ÉTAPE 2 : Préparation du contexte historique
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\n[HISTORIQUE PRÉCÉDENT] : {latest_past['report_text'][:1000]}"

    instructions = f"""Tu es un Agent Senior en Intelligence Stratégique.
    Voici le contenu textuel brut que je viens d'extraire de la cible ({target}) :
    ---
    {contenu_site}
    ---
    
    TA MISSION : Analyser ce contenu pour détecter la stratégie actuelle.
    {comp_context}

    FORMAT DE RAPPORT :
    1. 📌 HIGHLIGHTS : Les 3 points clés.
    2. 💻 STOREFRONT : Analyse de l'offre visible.
    3. 🏆 MAPPING : Produits phares et prix détectés.
    4. 🔮 PRÉDICTION : Évolution à 3 mois.

    STRICT : Si le contenu fourni est vide ou contient une erreur, base-toi sur tes connaissances de la marque mais signale-le."""

    try:
        # On utilise gemini-1.5-flash qui est très stable et rapide
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instructions)
        prompt = f"Analyse stratégique de {target}. Focus particulier sur : {focus}."
        
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
    target_input = col1.text_input("URL (ex: https://www.5five.com/fr/) :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Extraction et Analyse en cours..."):
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
