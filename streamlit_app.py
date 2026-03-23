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

# --- CONFIGURATION DE L'AGENT (STYLE AI STUDIO) ---
instructions = """Tu es un Expert en Intelligence Stratégique de haut niveau. 
Ta mission est d'analyser une marque ou une URL de façon NEUTRE et FACTUELLE. 
Ne fais aucune comparaison avec d'autres marques sauf si demandé.

Tu DOIS impérativement structurer ton rapport comme suit :
1. TITRE : RAPPORT DE VEILLE STRATÉGIQUE QUOTIDIEN : [NOM DE LA CIBLE]
2. META : Date d'analyse, Cible et Introduction brève.
3. 📌 HIGHLIGHTS : Les 3 faits marquants du jour (analyser les changements récents, blog, promos).
4. 🏆 TOP 5 DES PRODUITS PHARES : Pour chaque produit, précise : Prix, Design/Matériaux, Distribution, Stratégie Marketing et Indices de succès.
5. 🎨 ANALYSE DE L'IDENTITÉ VISUELLE : Couleurs, Tendances, Type de photos & Slogan.
6. 🔮 PRÉDICTION STRATÉGIQUE : Tes prévisions pour les 3 prochains mois.
7. 🔗 SOURCES : Liste exhaustive des URLs exactes consultées.

Utilise des citations numérotées [1], [2] dans le texte qui renvoient à ta section Sources."""

model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction=instructions,
    tools=[{'google_search': {}}] # Activation de la recherche en temps réel
)

# --- INTERFACE (Paramètres conservés) ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Paramètres")
    target = st.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
    focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    btn = st.button("Lancer la veille stratégique", use_container_width=True)

with col2:
    if btn:
        with st.spinner("Recherche et analyse des données en cours..."):
            try:
                today = datetime.now().strftime("%d %B %Y")
                prompt = f"Réalise l'analyse stratégique de {target} au {today}. Focus : {focus}."
                
                # Génération du contenu
                response = model.generate_content(prompt)
                
                st.markdown(response.text)
                st.success("Analyse terminée avec succès.")
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
    else:
        st.info("Modifiez les paramètres à gauche et lancez l'analyse.")
