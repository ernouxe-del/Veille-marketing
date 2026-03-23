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

# --- 3. BIBLIOTHÈQUE DE CERVEAUX ---
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
    "💰 Expert Pricing": "Focus exclusif sur les prix de {target}.",
    "🎨 Expert Design": "Focus exclusif sur la DA de {target}."
}

# --- 4. FONCTION D'ANALYSE ---
def executer_analyse(target, focus, instructions_cerveau):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante.")
        st.stop()
    
    # Configuration explicite de l'API
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Le nom correct de l'outil pour éviter l'erreur "Unknown field" (image_5a4b28)
    tools_config = [{"google_search_retrieval": {}}]
    
    try:
        # On utilise 'gemini-1.5-flash' sans passer par la version beta si possible
        # Ou on force le modèle qui accepte la recherche web
        model = genai.GenerativeModel(
            model_name='models/gemini-1.5-flash', # Ajout du préfixe 'models/' pour la stabilité
            system_instruction=instructions_cerveau.format(target=target),
            tools=tools_config
        )
        
        prompt = f"Effectue une veille stratégique complète sur {target}. Focus : {focus}."
        
        # On spécifie explicitement la version de l'API si le SDK le permet, 
        # sinon on laisse le SDK gérer mais avec le bon nom de modèle.
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        error_str = str(e)
        # Gestion du Quota (image_5aceaa)
        if "429" in error_str:
            return "⏳ **Quota atteint** : Le plan gratuit limite les requêtes. Attends 60 secondes."
        
        # Si le 404 persiste (image_5abc41), on tente un modèle alternatif sans recherche en secours
        if "404" in error_str:
            try:
                model_alt = genai.GenerativeModel('gemini-1.5-pro')
                response = model_alt.generate_content(f"Analyse rapide de {target} (Mode secours sans recherche live).")
                return "⚠️ *Note : Mode secours activé (recherche live indisponible).* \n\n" + response.text
            except:
                return f"❌ Erreur critique persistante : {e}"
        
        return f"❌ Erreur technique : {e}"

# --- 5. SIDEBAR (GESTION HISTORIQUE & CERVEAU) ---
with st.sidebar:
    st.title("🕵️‍♂️ Configuration")
    
    # Choix du cerveau
    choix_nom = st.selectbox("Sélectionne le cerveau :", list(CERVEAUX.keys()))
    instructions_custom = st.text_area("Instructions actives :", value=CERVEAUX[choix_nom], height=300)

    st.markdown("---")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("### 🏢 Marques suivies")
    all_data = db.all()
    unique_targets = sorted(list(set([ana['target_name'] for ana in all_data])))
    
    for t_name in unique_targets:
        cols = st.columns([0.7, 0.3])
        if cols[0].button(f"🏢 {t_name}", key=f"btn_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        # BOUTON SUPPRIMER RETABLIT
        if cols[1].button("🗑️", key=f"del_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

# --- 6. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Lancer une veille stratégique")
    col1, col2 = st.columns(2)
    target_input = col1.text_input("URL cible :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus :", ["Global", "Nouveautés", "Prix"])
    
    if st.button("🚀 Lancer l'analyse"):
        with st.spinner("Recherche en direct et analyse..."):
            report = executer_analyse(target_input, focus_input, instructions_custom)
            t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
            # Sauvegarde SANS écraser (Nouvel ID unique)
            db.insert({
                'id': str(uuid.uuid4()),
                'target': target_input,
                'target_name': t_name,
                'timestamp': datetime.now().timestamp(),
                'report_text': report,
                'focus': focus_input
            })
            st.session_state['selected_target'] = t_name
            st.rerun()
else:
    # Récupération de toutes les analyses pour cette marque
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    
    col_title, col_refresh = st.columns([0.7, 0.3])
    col_title.header(f"Rapports : {selected_target}")
    
    # BOUTON RAFRAICHIR RETABLIT (Crée une nouvelle entrée en base)
    if col_refresh.button("🔄 Actualiser (Nouvelle Archive)"):
        with st.spinner("Mise à jour du rapport..."):
            new_report = executer_analyse(reports[0]['target'], reports[0]['focus'], instructions_custom)
            db.insert({
                'id': str(uuid.uuid4()),
                'target': reports[0]['target'],
                'target_name': selected_target,
                'timestamp': datetime.now().timestamp(),
                'report_text': new_report,
                'focus': reports[0]['focus']
            })
            st.rerun()

    st.markdown("---")
    st.subheader("📍 Dernière version")
    st.markdown(reports[0]['report_text'])
    
    # SYSTÈME D'ARCHIVES POUR NE PAS PERDRE LES JOURS PRÉCÉDENTS
    if len(reports) > 1:
        st.markdown("---")
        st.subheader("📜 Historique des analyses")
        for old in reports[1:]:
            date_str = datetime.fromtimestamp(old['timestamp']).strftime('%d/%m/%Y à %H:%M')
            with st.expander(f"Analyse du {date_str}"):
                st.markdown(old['report_text'])
