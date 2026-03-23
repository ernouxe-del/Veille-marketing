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

# --- 3. BIBLIOTHÈQUE DE CERVEAUX (Ton prompt AI Studio intégré ici) ---
CERVEAUX = {
    "🧠 Agent Standard (AI Studio)": """Role: You are a Senior Strategic Intelligence Agent specialized in competitive monitoring. Your goal is to detect every subtle change in the strategy of {target}.

Source of Truth: Your primary target is {target}. You must explore the site globally to detect changes and recent news indexed by Google Search.

Analysis Pillars:
1. Pricing Strategy: Monitor any price fluctuations, new discount patterns, or psychological pricing changes.
2. Product Catalog: Detect new arrivals ("New In" section) and discontinued items.
3. Visual Identity (DA): Analyze changes in photography style, color palettes, font usage, and website layout. 
4. Trend Scouting: Identify emerging themes, keywords, or marketing slogans used in their latest campaigns.

Product Mapping Duties:
Structure report by category (Kitchen, Storage, Bathroom, Furniture, etc.):
- Core Offering: Identify the top-selling/most visible products.
- Price Architecture: Define the price brackets (e.g., Entry-level: 2€-10€, Mid-range: 15€-45€, Premium: 50€+).
- Materials & Specs: Note recurring materials (Bambou, Inox, Plastic recycled) to detect shifts in quality/margin.

Mandatory Product Report Format:
1. Product Name & Range
2. Current Price (min/max/average)
3. Design Analysis (materials, colors, aesthetic style)
4. Distribution (where it's available)
5. Marketing Hook (how the brand presents it visually and its main promise)

Output Rules:
- ALWAYS respond in French.
- Use a professional, analytical tone.
- Start each report with a "Highlights" section (the 3 most important changes).
- End with a "Strategic Prediction" (what this means for their next 3 months).

Constraint: If data is missing, mention it clearly and suggest a specific search query. No Click & Collect or CSR mention if not found.""",

    "💰 Expert Pricing": "Focus exclusif sur les prix et les marges de {target}.",
    "🎨 Expert Design": "Focus exclusif sur la DA et le style visuel de {target}."
}

# --- 4. FONCTION D'ANALYSE (ACTIVATION RECHERCHE GOOGLE) ---
def executer_analyse(target, focus, instructions_cerveau):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante.")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Outil de recherche indispensable pour la précision "AI Studio"
    tools_config = [{"google_search_retrieval": {}}]
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=instructions_cerveau.format(target=target),
            tools=tools_config
        )
        
        prompt = f"Réalise l'analyse stratégique de {target}. Focus : {focus}. Utilise la recherche Google pour les données du jour."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⏳ Quota dépassé. Attends 1 minute."
        return f"Erreur technique : {e}"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🕵️‍♂️ Configuration Agent")
    choix_nom = st.selectbox("Sélectionne le cerveau :", list(CERVEAUX.keys()))
    instructions_custom = st.text_area("Instructions actives :", value=CERVEAUX[choix_nom], height=400)

    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 Historique")
    targets = sorted(list(set([ana['target_name'] for ana in db.all()])))
    for t in targets:
        if st.button(f"🏢 {t}", key=f"t_{t}"):
            st.session_state['selected_target'] = t
            st.rerun()

# --- 6. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer une veille stratégique")
    col1, col2 = st.columns(2)
    target_input = col1.text_input("URL cible :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Nouveautés", "Prix"])
    
    if st.button("Lancer l'analyse"):
        with st.spinner("Recherche en direct et analyse..."):
            report = executer_analyse(target_input, focus_input, instructions_custom)
            t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
            db.insert({'target_name': t_name, 'timestamp': datetime.now().timestamp(), 'report_text': report})
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    st.header(f"Rapport : {selected_target}")
    st.markdown(reports[0]['report_text'])
