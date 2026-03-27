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
        st.info(f"🔎 Exploration de la structure actuelle de {base_url}...")
        reader_url = f"https://r.jina.ai/{base_url}"
        response = requests.get(reader_url, timeout=25)
        home_text = response.text if response.status_code == 200 else ""
        
        mots_cles = ["nouveau", "new", "ventes", "best", "top", "promo", "soldes", "collection"]
        liens_trouves = re.findall(r'\(https?://[^\s\)]+\)', home_text)
        liens_propres = [l.strip('()') for l in liens_trouves]
        
        urls_a_visiter = [base_url]
        domain = base_url.split('//')[-1].split('/')[0]
        for link in liens_propres:
            if any(mot in link.lower() for mot in mots_cles) and domain in link:
                if link not in urls_a_visiter:
                    urls_a_visiter.append(link)
        
        urls_a_visiter = list(dict.fromkeys(urls_a_visiter))[:3]
        
        scan_global = ""
        for url in urls_a_visiter:
            nom_page = url.split('/')[-1] or "Accueil"
            st.info(f"📄 Lecture approfondie : {nom_page}")
            try:
                res = requests.get(f"https://r.jina.ai/{url}", timeout=30)
                if res.status_code == 200:
                    scan_global += f"\n\n--- DONNÉES DE LA PAGE : {url} ---\n"
                    scan_global += res.text[:8000]
            except:
                continue
                
        return scan_global
    except Exception as e:
        return f"Erreur lors de l'exploration : {e}"

# --- 4. LE CERVEAU DE L'AGENT (IA Comparative) ---
def executer_analyse(target, focus):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 1. On récupère les données fraîches du site
    donnees_futures = decouvrir_et_scanner(target)

    # 2. On récupère TOUT l'historique pour la comparaison
    past_analyses = db.search(Analysis.target == target)
    comp_context = "C'est la première veille pour ce site."
    if past_analyses:
        latest = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"VOICI LE RAPPORT PRÉCÉDENT (À COMPARER) :\n---\n{latest['report_text']}\n---"

    # 3. Prompt avec la structure exigée et le focus comparatif
    prompt = f"""Tu es un Agent Senior en Intelligence Stratégique. 
    Ta mission est d'analyser le site {target} et de détecter TOUTES les évolutions par rapport au rapport précédent.
    
    VOICI LES DONNÉES DU SCAN ACTUEL :
    --- 
    {donnees_futures}
    ---
    
    {comp_context}

    TU DOIS RÉDIGER TON RAPPORT SELON CETTE STRUCTURE STRICTE :

    1. 📢 ANALYSE GLOBALE & FAITS NOTABLES :
       Analyse ce que le site met en avant aujourd'hui (Hero Banner, message principal, événement saisonnier).
       Quels sont les faits marquants de cette visite ?

    2. 🏗️ ARCHITECTURE & STRUCTURE DU SITE :
       Analyse le menu et les catégories. 
       COMPARAISON OBLIGATOIRE : Dis-moi précisément si la structure a changé par rapport au rapport précédent (nouveaux onglets, catégories supprimées ou renommées).

    3. 🏷️ OFFRE PRODUITS, PRIX & PROMOTIONS :
       Regroupe ici tout le concret :
       - Liste des Nouveautés (New In) avec prix.
       - Liste des Best-Sellers (Top ventes).
       - Analyse des promotions actuelles.
       COMPARAISON OBLIGATOIRE : Note les changements de prix ou les nouveaux produits par rapport à la dernière fois.

    4. 🔮 TENDANCE GLOBALE & PRÉDICTION :
       Quels styles dominent ? Quelle est ta prédiction stratégique pour les 3 prochains mois ?

    CONSIGNE : Si tu ne vois aucun changement sur un point, écris "Structure inchangée". Sois factuel et cite des produits."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

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
    st.header("Lancer un Agent de Veille Comparative")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL de la marque :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer l'Analyse"):
        with st.spinner("L'agent explore et compare les données..."):
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
    
    if st.button("🔄 Actualiser & Comparer"):
        with st.spinner("Scan profond et analyse des différences..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_report, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.markdown(reports[0]['report_text'])
