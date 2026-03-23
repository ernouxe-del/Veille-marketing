import streamlit as st
import google.generativeai as genai
from datetime import datetime

# 1. Configuration de l'interface
st.set_page_config(page_title="Agent Veille 5five", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Agent d'Intelligence Stratégique : 5five & Co")
st.markdown("---")

# 2. Connexion
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. Configuration de l'IA (Optimisée Marché FR + Analyse URL)
instructions_strategiques = """Tu es un Expert en Intelligence Stratégique spécialisé sur le MARCHÉ FRANÇAIS. 
Ta mission est d'analyser la cible de façon NEUTRE et FACTUELLE.

DIRECTIVES SPÉCIFIQUES :
- FOCUS GÉOGRAPHIQUE : Analyse exclusivement les tendances, prix et comportements de consommation en FRANCE.
- ANALYSE URL POUSSÉE : Explore l'arborescence, les catégories de produits, le tunnel de vente et la stratégie de contenu du site fourni.
- NEUTRALITÉ : Pas de comparaison avec 5five ou d'autres marques.

STRUCTURE DU RAPPORT :
1. 📌 HIGHLIGHTS FR : Les 3 faits marquants récents sur le marché français.
2. 🏆 TOP 5 PRODUITS (MARCHÉ FR) : Analyse détaillée (Prix en €, Design, Distribution France, Stratégie).
3. 💻 AUDIT DU SITE WEB : Analyse de l'expérience utilisateur, de l'arborescence et de l'efficacité commerciale de l'URL.
4. 🎨 IDENTITÉ VISUELLE : Couleurs, Style et Slogan adaptés au public français.
5. 🔮 PRÉDICTION (3 MOIS) : Tendances à venir sur le secteur en France.
6. 🔗 SOURCES : URLs précises consultées."""

model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction=instructions_strategiques
)

# 4. Interface utilisateur
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Paramètres")
    target = st.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
    focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    btn = st.button("Lancer la veille stratégique", use_container_width=True)

with col2:
    if btn:
        with st.spinner("Analyse approfondie du marché français et de l'URL..."):
            try:
                today = datetime.now().strftime("%d %B %Y")
                # Prompt enrichi pour forcer l'analyse de l'URL
                prompt = f"""Effectue une analyse stratégique poussée de l'URL {target}. 
                Le focus doit être mis sur le marché FRANÇAIS et sur l'aspect {focus}.
                Décortique la structure du site et les offres actuelles au {today}."""
                
                response = model.generate_content(prompt)
                
                st.success("Analyse France terminée !")
                st.markdown(response.text)
                st.balloons()
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
    else:
        st.info("Entrez une cible à gauche pour générer le rapport stratégique France.")

st.sidebar.markdown("---")
st.sidebar.write("⚡ Mode : Expert Marché Français")
