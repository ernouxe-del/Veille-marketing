import streamlit as st
import google.generativeai as genai
from datetime import datetime

# 1. Configuration de l'interface (Ta base validée)
st.set_page_config(page_title="Agent Veille 5five", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Agent d'Intelligence Stratégique : 5five & Co")
st.markdown("---")

# 2. Connexion
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. Configuration de l'IA (On garde gemini-3-flash-preview mais on change le comportement)
instructions_strategiques = """Tu es un Expert en Intelligence Stratégique. 
Ta mission est d'analyser la cible de façon NEUTRE et FACTUELLE. 
Ne fais aucune comparaison avec 5five ou d'autres marques, reste concentré sur la cible.

Structure ton rapport exactement ainsi :
1. 📌 HIGHLIGHTS : Les 3 faits marquants récents (blog, actus, nouveautés).
2. 🏆 TOP 5 DES PRODUITS PHARES : Pour chaque produit : Prix, Design, Distribution, Stratégie et Succès.
3. 🎨 ANALYSE DE L'IDENTITÉ VISUELLE : Couleurs, Style de photos, Slogan.
4. 🔮 PRÉDICTION STRATÉGIQUE : Tes prévisions pour les 3 prochains mois.
5. 🔗 SOURCES : Liste les URLs précises que tu as utilisées pour cette analyse."""

model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction=instructions_strategiques
)

# 4. Interface utilisateur (On garde tes paramètres préférés)
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Paramètres")
    target = st.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
    focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    btn = st.button("Lancer la veille stratégique", use_container_width=True)

with col2:
    if btn:
        with st.spinner("L'IA analyse les données en temps réel..."):
            try:
                today = datetime.now().strftime("%d %B %Y")
                # On demande explicitement d'aller chercher les sources
                prompt = f"Réalise l'analyse stratégique neutre de {target} au {today}. Focus : {focus}. N'oublie pas de citer tes sources à la fin."
                
                response = model.generate_content(prompt)
                
                st.success("Analyse terminée !")
                st.markdown(response.text)
                st.balloons()
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
    else:
        st.info("Entrez une cible à gauche et cliquez sur le bouton pour générer le rapport.")

st.sidebar.markdown("---")
st.sidebar.write("⚡ Propulsé par Gemini 3 Flash")
