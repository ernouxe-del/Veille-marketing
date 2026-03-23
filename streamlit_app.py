import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1c22; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .date-badge { background-color: #343541; padding: 5px 10px; border-radius: 10px; font-size: 0.8rem; color: #ccc; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. LOGIQUE D'ANALYSE ---
def executer_analyse(target, focus):
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # On récupère TOUT l'historique de cette cible pour que l'IA compare
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\nCONTEXTE HISTORIQUE PRÉCÉDENT : {latest_past['report_text'][:1000]}"

    instructions = f"""Tu es un Expert en Intelligence Stratégique (Marché FR). 
    Analyse la cible de façon NEUTRE. Focus : {focus}.
    STRUCTURE : 1. Highlights FR, 2. Digital Storefront (Univers & Merchandising), 3. Top 5 Produits, 4. Analyse Comparative (évolution par rapport au passé), 5. Identité & Prévisions, 6. Sources."""

    model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=instructions)
    response = model.generate_content(f"Analyse {target} au {datetime.now()}. {comp_context}")
    return response.text

# --- 4. SIDEBAR (Groupée par Marque) ---
with st.sidebar:
    st.title("🕵️‍♂️ Mes Veilles")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 Marques suivies")
    
    # On récupère les marques uniques
    all_data = db.all()
    unique_targets = sorted(list(set([ana['target_name'] for ana in all_data])))
    
    for t_name in unique_targets:
        cols = st.columns([0.8, 0.2])
        if cols[0].button(f"🏢 {t_name}", key=f"target_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        # Suppression de toute la marque et son historique
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
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Analyse initiale en cours..."):
            try:
                report_text = executer_analyse(target_input, focus_input)
                t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
                db.insert({
                    'id': str(uuid.uuid4()),
                    'target': target_input,
                    'target_name': t_name,
                    'timestamp': datetime.now().timestamp(),
                    'report_text': report_text,
                    'focus': focus_input
                })
                st.session_state['selected_target'] = t_name
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    # AFFICHAGE DE LA TIMELINE POUR UNE MARQUE
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    
    col_t, col_up = st.columns([0.7, 0.3])
    col_t.header(f"Veille : {selected_target}")
    
    if col_up.button("🔄 Actualiser (Nouvelle version)"):
        with st.spinner("Analyse des changements en cours..."):
            new_text = executer_analyse(reports[0]['target'], reports[0]['focus'])
            db.insert({
                'id': str(uuid.uuid4()),
                'target': reports[0]['target'],
                'target_name': selected_target,
                'timestamp': datetime.now().timestamp(),
                'report_text': new_text,
                'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")

    # Affichage du rapport le plus récent
    st.subheader("📍 Dernière Analyse")
    st.info(f"Établie le {datetime.fromtimestamp(reports[0]['timestamp']).strftime('%d/%m/%Y à %H:%M')}")
    st.markdown(reports[0]['report_text'])
    
    # Affichage des archives en dessous
    if len(reports) > 1:
        st.markdown("---")
        st.subheader("📜 Archives de cette marque")
        for i, old_ana in enumerate(reports[1:]):
            with st.expander(f"Version du {datetime.fromtimestamp(old_ana['timestamp']).strftime('%d/%m/%Y')}"):
                st.markdown(old_ana['report_text'])

    if st.button("⬅️ Retour"):
        st.session_state['selected_target'] = None
        st.rerun()
