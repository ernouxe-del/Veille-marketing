import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid
import requests
import re

# --- 1. CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Agent Veille Stratégique Pro", page_icon="🕵️‍♂️", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1c22; }
    .stButton>button { width: 100%; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): 
    os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. L'OEIL DE L'AGENT (Exploration Multi-Pages) ---
def decouvrir_et_scanner(base_url):
    """L'agent explore la home page pour trouver les liens vers les nouveautés et les tops."""
    try:
        # 1. Lecture de la Home Page pour trouver les liens
        st.info(f"🔎 Exploration de la structure de {base_url}...")
        reader_url = f"https://r.jina.ai/{base_url}"
        response = requests.get(reader_url, timeout=15)
        home_text = response.text if response.status_code == 200 else ""
        
        # 2. Recherche de liens stratégiques (Nouveautés, Best-sellers, Promo)
        # Jina renvoie du Markdown, les liens sont au format [texte](url)
        mots_cles = ["nouveau", "new", "ventes", "best", "top", "promo", "soldes", "collection"]
        liens_trouves = re.findall(r'\(https?://[^\s\)]+\)', home_text)
        # On nettoie les parenthèses
        liens_propres = [l.strip('()') for l in liens_trouves]
        
        urls_a_visiter = [base_url]
        
        # On sélectionne les liens les plus pertinents qui appartiennent au même site
        for link in liens_propres:
            if any(mot in link.lower() for mot in mots_cles) and base_url.split('//')[-1].split('/')[0] in link:
                if link not in urls_a_visiter:
                    urls_a_visiter.append(link)
        
        # On limite le scan à 4 pages maximum pour la rapidité
        urls_a_visiter = list(dict.fromkeys(urls_a_visiter))[:4]
        
        scan_global = ""
        for url in urls_a_visiter:
            nom_page = url.split('/')[-1] or "Accueil"
            st.info(f"📄 Lecture approfondie : {nom_page}")
            res = requests.get(f"https://r.jina.ai/{url}", timeout=15)
            if res.status_code == 200:
                scan_global += f"\n\n--- DONNÉES DE LA PAGE : {url} ---\n"
                scan_global += res.text[:8000] # On prend un gros morceau de texte
                
        return scan_global
    except Exception as e:
        return f"Erreur lors de l'exploration : {e}"

# --- 4. LE CERVEAU DE L'AGENT (IA) ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Étape 1 : Exploration réelle du site
    donnees_brutes = decouvrir_et_scanner(target)

    # Étape 2 : Contexte historique
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n[RAPPEL DE TON ANALYSE PRÉCÉDENTE] : {latest['report_text'][:1000]}"

    # Étape 3 : Construction du prompt stratégique
    prompt = f"""Tu es un Agent Senior en Intelligence Stratégique expert en E-commerce.
    Tu as scanné plusieurs pages stratégiques du site {target}.
    
    VOICI TOUTES LES DONNÉES RÉCUPÉRÉES (Home, Nouveautés, Tops) :
    --- 
    {donnees_brutes}
    ---
    
    {comp_context}

    TA MISSION : 
    Produire un rapport de veille concurrentielle ULTRA-PRÉCIS. 
    Ne fais pas de généralités. Je veux des preuves concrètes.
    
    STRUCTURE DU RAPPORT EXIGÉE :
    1. 🚀 NOUVEAUTÉS DÉTECTÉES : Liste les noms exacts des nouveaux produits (New In) et leurs prix si visibles.
    2. 🏆 BEST-SELLERS & TOPS : Identifie les produits mis en avant comme les meilleures ventes.
    3. 💰 ANALYSE PRIX & PROMOS : Détaille les offres commerciales actuelles (ex: -20% sur la déco).
    4. 🔮 TENDANCE & PRÉDICTION : Basé sur ces objets précis, quelle est la tendance de la marque (ex: styles, couleurs) ?
    
    CONSIGNE : Cite les noms des produits pour prouver que tu les as bien vus."""

    try:
        # Utilisation de gemini-2.5-flash (actif sur ton compte)
        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"L'agent a rencontré une erreur IA : {e}"

# --- 5. SIDEBAR (Historique) ---
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
        if cols[0].button(f"🏢 {t_name}", key=f"t_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        if cols[1].button("🗑️", key=f"del_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

# --- 6. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer un Agent de Veille Profonde")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL de la marque :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer l'Agent Explorateur"):
        with st.spinner("L'agent explore les différentes pages du site (Nouveautés, Tops...)..."):
            report = executer_analyse(target_input, focus_input)
            t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
            db.insert({
                'id': str(uuid.uuid4()), 'target': target_input, 'target_name': t_name,
                'timestamp': datetime.now().timestamp(), 'report_text': report, 'focus': focus_input
            })
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    st.header(f"Rapport : {selected_target}")
    
    if st.button("🔄 Actualiser (Deep Scan)"):
        with st.spinner("Re-scan complet du site en cours..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_report, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.markdown(reports[0]['report_text'])
