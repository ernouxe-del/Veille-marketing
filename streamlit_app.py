import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

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

# --- 3. BIBLIOTHÈQUE DE CERVEAUX ---
CERVEAUX = {
    "🧠 Expert Standard (AI Studio)": """Tu es un Agent Senior en Intelligence Stratégique. Ton but est de détecter chaque changement subtil de stratégie.
SOURCES DE VÉRITÉ : Ta cible primaire est {target}. 
PILIERS : Stratégie de prix, Catalogue, Identité Visuelle, Merchandising par UNIVERS.
CONSTRAINTE : NE RIEN INVENTER (RSE/Click & Collect).""",

    "💰 Expert Pricing & Promo": """Tu es un Analyste financier spécialisé en Retail. Ton focus est à 100% sur la rentabilité et les prix de {target}.
ANALYSE : Repère les prix psychologiques, les mécaniques de promotion (ex: -20% sur le 2ème) et compare l'entrée vs haut de gamme.
LIVRABLE : Tableau des prix et architecture tarifaire par univers.""",

    "🎨 Expert Design & DA": """Tu es un Directeur Artistique Senior. Analyse l'image de marque de {target}.
FOCUS : Photographie, colorimétrie, typographie et "vibe" marketing.
PRODUITS : Identifie les 5 produits les plus esthétiques et explique pourquoi ils sont mis en avant."""
}

# --- 4. FONCTION D'ANALYSE ---
def executer_analyse(target, focus, instructions_cerveau):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante.")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Historique pour comparaison
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\n[HISTORIQUE PRÉCÉDENT] : {latest_past['report_text'][:1000]}"

    # Construction du prompt final
    full_instructions = f"{instructions_cerveau.format(target=target)}\n{comp_context}"
    
    try:
        # Utilisation de 1.5-flash pour la stabilité
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=full_instructions)
        prompt = f"Effectue un rapport complet sur {target}. Focus : {focus}."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur technique : {e}"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🕵️‍♂️ Configuration")
    
    # MENU DÉROULANT POUR LE CERVEAU
    st.subheader("🤖 Choix du Cerveau")
    choix_nom = st.selectbox("Sélectionne un profil :", list(CERVEAUX.keys()))
    
    # Zone de texte modifiable au cas où on veut ajuster le prompt choisi
    instructions_custom = st.text_area("Ajuster les instructions :", value=CERVEAUX[choix_nom], height=200)

    st.markdown("---")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
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
            st.rerun()

# --- 6. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Nouvelle Analyse Stratégique")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL ou Marque :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner(f"Analyse avec le profil {choix_nom} en cours..."):
            report_text = executer_analyse(target_input, focus_input, instructions_custom)
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
            new_text = executer_analyse(reports[0]['target'], reports[0]['focus'], instructions_custom)
            db.insert({
                'id': str(uuid.uuid4()), 'target': reports[0]['target'], 'target_name': selected_target,
                'timestamp': datetime.now().timestamp(), 'report_text': new_text, 'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.markdown(reports[0]['report_text'])
