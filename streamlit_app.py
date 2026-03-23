import streamlit as st
import google.generativeai as genai
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent Veille Stratégique - Flash 1.5", layout="wide")

# Initialisation de la clé API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Clé API manquante dans les secrets Streamlit.")
    st.stop()

# --- FONCTION D'ANALYSE (RETOUR À 1.5 FLASH) ---
def executer_analyse(target, focus, system_prompt):
    """
    Exécute l'analyse avec Gemini 1.5 Flash et l'outil de recherche.
    """
    # Utilisation du nom d'outil correct pour éviter l'erreur 'Unknown field'
    tools_config = [{"google_search_retrieval": {}}]
    
    try:
        # Basculement sur gemini-1.5-flash pour plus de stabilité de quota
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt,
            tools=tools_config
        )
        
        prompt_utilisateur = f"""
        Réalise une veille stratégique sur : {target}
        Focus : {focus}
        Date : {datetime.date.today().strftime('%d %B %Y')}
        
        IMPORTANT : Utilise Google Search pour obtenir les données réelles du jour 
        et inclus les sources [1], [2] comme dans AI Studio.
        """
        
        response = model.generate_content(prompt_utilisateur)
        
        if not response.text:
            return "L'IA n'a pas pu générer de réponse. Réessaie."
            
        return response.text

    except Exception as e:
        error_msg = str(e)
        # Gestion du Quota (Erreur 429)
        if "429" in error_msg:
            return "⏳ **Quota atteint** : Gemini 1.5 Flash est sollicité. Attends 30 secondes avant de cliquer à nouveau."
        
        # Gestion des erreurs de configuration (404)
        if "404" in error_msg:
            return "❌ **Erreur 404** : Le modèle ou l'outil rencontre un problème technique temporaire."
            
        return f"❌ **Erreur technique** : {error_msg}"

# --- INTERFACE ---
st.title("🕵️ Veille Stratégique (Mode Flash 1.5)")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Rappel du prompt expert marché français
    prompt_expert = """Tu es un Agent Senior expert du marché français de l'équipement de la maison.
Analyse de façon ultra-factuelle.
Structure :
1. HIGHLIGHTS FR (3 faits marquants)
2. TOP 5 PRODUITS (Prix, Design, Preuves de succès)
3. DIRECTION ARTISTIQUE & VISUELLE
4. PRÉDICTIONS STRATÉGIQUES"""
    
    system_prompt = st.text_area("Cerveau de l'IA :", value=prompt_expert, height=250)
    st.divider()
    st.caption("Modèle : Gemini 1.5 Flash (Optimisé Quota)")

# Formulaire
col1, col2 = st.columns([1, 2])

with col1:
    target_url = st.text_input("URL à surveiller :", value="https://www.5five.com/fr/")
    analysis_focus = st.selectbox("Type d'analyse :", ["Global", "Prix", "Nouveautés"])
    
    if st.button("🚀 Lancer l'analyse", use_container_width=True):
        with st.spinner("Recherche en direct..."):
            resultat = executer_analyse(target_url, analysis_focus, system_prompt)
            st.session_state['resultat_flash'] = resultat

with col2:
    if 'resultat_flash' in st.session_state:
        st.subheader("Rapport Factuel 📍")
        st.markdown(st.session_state['resultat_flash'])
    else:
        st.info("Les résultats de l'analyse s'afficheront ici.")
