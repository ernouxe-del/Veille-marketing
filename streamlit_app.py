import streamlit as st
import google.generativeai as genai
from datetime import datetime

# Configuration de l'interface
st.set_page_config(page_title="Agent Veille 5five", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Agent d'Intelligence Stratégique : 5five & Co")
st.markdown("---")

# Connexion sécurisée
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- CONFIGURATION DE L'AGENT ---
instructions = """Tu es un Expert en Intelligence Stratégique. 
Analyse la marque ou l'URL fournie de façon NEUTRE et FACTUELLE. 
Structure ton rapport avec : Highlights, Top 5 Produits, Identité Visuelle, Prédictions et Sources."""

# On définit l'outil de recherche de façon plus simple pour éviter le bug
tools_config = [{"google_search_retrieval": {}}]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', # On repasse sur 1.5 pour garantir la stabilité de la recherche
    system_instruction=instructions,
    tools=tools_config
)

# --- INTERFACE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Paramètres")
    target = st.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
    focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    btn = st.button("Lancer la veille stratégique", use_container_width=True)

with col2:
    if btn:
        with st.spinner("Recherche et analyse en cours..."):
            try:
                today = datetime.now().strftime("%d %B %Y")
                prompt = f"Réalise l'analyse stratégique de {target} au {today}. Focus : {focus}. Utilise tes outils de recherche pour trouver les dernières infos."
                
                # Génération
                response = model.generate_content(prompt)
                
                if response.text:
                    st.markdown(response.text)
                    st.success("Analyse terminée.")
                else:
                    st.warning("L'IA n'a pas pu générer de texte. Réessaie.")
            except Exception as e:
                st.error(f"Erreur technique : {e}")
                st.info("Conseil : Si l'erreur persiste, essaie de retirer la ligne 'tools=tools_config' dans le code.")
