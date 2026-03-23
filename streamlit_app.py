import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. LOGIQUE D'ANALYSE AVEC GOOGLE SEARCH ---
def executer_analyse(target, focus, system_prompt):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante.")
        return "Erreur"
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 1. On utilise le nom d'outil qui fonctionne sur la version 2.0
    tools_config = [{"google_search_retrieval": {}}]
    
   try:
    response = model.generate_content(prompt)
    return response.text
except Exception as e:
    if "429" in str(e):
        return "⏳ **Pause forcée par Google (Quota)** : Patiente 60 secondes. L'IA a besoin de souffler pour rester gratuite !"
    return f"Erreur : {e}"

    except Exception as e:
        # 3. Système de secours intelligent (Fallback)
        # Si le 404 persiste avec l'outil de recherche, on lance sans l'outil
        if "404" in str(e) or "not supported" in str(e).lower():
            st.warning("Recherche Web désactivée par l'API (Mode local activé).")
            model_simple = genai.GenerativeModel('gemini-2.0-flash', system_instruction=system_prompt)
            response = model_simple.generate_content(f"Analyse de {target} (Focus: {focus})")
            return response.text
            
        return f"Erreur technique : {e}"
# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🕵️‍♂️ Configuration")
    
    # ÉDITEUR DE CERVEAU (Comme dans AI Studio)
    with st.expander("🧠 Modifier le Cerveau (System Prompt)", expanded=False):
        custom_prompt = st.text_area("Instructions de l'agent :", value="""Tu es un Agent Senior en Intelligence Stratégique. 
Ta cible est l'URL fournie. Tu dois explorer le site via Google Search pour détecter les changements.

PILIERS :
1. Prix : Fluctuations et promos.
2. Catalogue : Nouveautés et fins de série.
3. Merchandising : Analyse par UNIVERS (Cuisine, Salle de bain, etc.).

FORMAT : 
- Highlights (3 points)
- Digital Storefront (Univers & Bannières)
- Top 5 Produits (Nom, Prix, Lien direct)
- Prédiction à 3 mois.

INTERDICTION D'INVENTER. Si tu ne trouves pas l'info (RSE, Click & Collect), n'en parle pas.""", height=400)

    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 Historique")
    all_data = db.all()
    unique_targets = sorted(list(set([ana['target_name'] for ana in all_data])))
    
    for t_name in unique_targets:
        cols = st.columns([0.8, 0.2])
        if cols[0].button(f"🏢 {t_name}", key=f"t_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        if cols[1].button("🗑️", key=f"d_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

# --- 5. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer une Veille")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL à analyser :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Démarrer l'analyse en temps réel"):
        with st.spinner("Recherche Google et analyse du site en cours..."):
            report = executer_analyse(target_input, focus_input, custom_prompt)
            t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
            db.insert({
                'id': str(uuid.uuid4()), 'target': target_input, 'target_name': t_name,
                'timestamp': datetime.now().timestamp(), 'report_text': report, 'focus': focus_input
            })
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    st.header(f"Veille : {selected_target}")
    
    if st.button("🔄 Actualiser (Recherche Google direct)"):
        with st.spinner("Mise à jour via recherche web..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'], custom_prompt)
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_report, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.markdown(reports[0]['report_text'])
    
    if len(reports) > 1:
        with st.expander("📜 Voir les versions précédentes"):
            for old in reports[1:]:
                st.write(f"**Analyse du {datetime.fromtimestamp(old['timestamp']).strftime('%d/%m/%Y')}**")
                st.markdown(old['report_text'])
                st.markdown("---")
