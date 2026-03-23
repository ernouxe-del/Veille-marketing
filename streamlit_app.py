import streamlit as st
import google.generativeai as genai
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent d'Intelligence Stratégique", layout="wide")

# Initialisation de la clé API via les secrets Streamlit
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Clé API manquante. Ajoute GOOGLE_API_KEY dans tes secrets Streamlit.")
    st.stop()

# --- FONCTION COEUR (CORRIGÉE) ---
def executer_analyse(target, focus, system_prompt):
    """
    Exécute l'analyse en utilisant Gemini 2.0 Flash avec l'outil de recherche.
    Gère les erreurs de quota (429) et de modèle (404).
    """
    # Utilisation du nom d'outil correct pour éviter l'erreur 'Unknown field'
    tools_config = [{"google_search_retrieval": {}}]
    
    try:
        # On utilise gemini-2.0-flash pour correspondre à tes tests réussis sur Studio
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt,
            tools=tools_config
        )
        
        # Construction du prompt utilisateur
        prompt_utilisateur = f"""
        Effectue une veille stratégique approfondie sur : {target}
        Focus de l'analyse : {focus}
        Date actuelle : {datetime.date.today().strftime('%d %B %Y')}
        
        Note : Utilise impérativement la recherche Google pour extraire des données réelles 
        et cite tes sources avec des indices [1], [2], etc.
        """
        
        response = model.generate_content(prompt_utilisateur)
        
        if not response.text:
            return "L'IA n'a pas retourné de texte. Vérifie tes paramètres."
            
        return response.text

    except Exception as e:
        error_msg = str(e)
        # Gestion du Quota Exceeded
        if "429" in error_msg:
            return "⏳ **Quota dépassé (Erreur 429)** : Google limite les requêtes sur le plan gratuit. Patiente 60 secondes avant de relancer."
        
        # Gestion du modèle non trouvé ou non supporté
        if "404" in error_msg or "not found" in error_msg.lower():
            return "❌ **Erreur de Modèle (404)** : Le modèle ou l'outil de recherche est indisponible. Vérifie ta région ou la version de ton SDK."
            
        return f"❌ **Erreur Technique** : {error_msg}"

# --- INTERFACE UTILISATEUR ---
st.title("🕵️ Agent d'Intelligence Stratégique : 5five & Co")

# Barre latérale pour la configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Éditeur de "Cerveau" (System Prompt) pour le mode Expert Marché Français
    default_prompt = """Tu es un Agent Senior expert du marché français de l'équipement de la maison. 
Ton objectif est de fournir une veille stratégique ultra-factuelle.
Structure ton rapport avec :
1. HIGHLIGHTS FR (3 faits marquants)
2. TOP 5 PRODUITS (Prix, Design, Succès)
3. DIRECTION ARTISTIQUE
4. PRÉDICTIONS À 3 MOIS"""
    
    system_prompt = st.text_area("Modifier le Cerveau (System Prompt) :", value=default_prompt, height=250)
    
    st.divider()
    st.info("Mode : Expert Marché Français activé ⚡")

# Formulaire principal
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Paramètres")
    target_url = st.text_input("URL ou Marque à surveiller :", value="https://www.5five.com/fr/")
    analysis_focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix & Promo", "Nouveautés", "Réseaux Sociaux"])
    
    if st.button("🚀 Lancer la veille stratégique", use_container_width=True):
        with st.spinner("Recherche Google et analyse en cours..."):
            resultat = executer_analyse(target_url, analysis_focus, system_prompt)
            st.session_state['dernier_rapport'] = resultat

with col2:
    st.subheader("Dernière Analyse Factuelle 📍")
    if 'dernier_rapport' in st.session_state:
        st.markdown(f"*Établie le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*")
        st.markdown("---")
        st.markdown(st.session_state['dernier_rapport'])
    else:
        st.write("Lancez une analyse pour voir les résultats s'afficher ici.")

# --- FOOTER ---
st.divider()
st.caption("Propulsé par Gemini 2.0 Flash avec Google Search Retrieval Tools.")
