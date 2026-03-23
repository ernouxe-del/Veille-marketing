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
# Utilisation de gemini-2.0-flash, le premier modèle de ta liste validée
instructions = """Tu es un Expert en Intelligence Stratégique. 
Analyse la cible de façon NEUTRE et FACTUELLE. 

Structure ton rapport exactement comme suit :
1. 📌 HIGHLIGHTS : Les 3 faits marquants récents.
2. 🏆 TOP 5 DES PRODUITS PHARES : (Prix, Design, Distribution, Stratégie, Succès).
3. 🎨 ANALYSE DE L'IDENTITÉ VISUELLE : Couleurs, Photos, Slogan.
4. 🔮 PRÉDICTION STRATÉGIQUE : Prévisions à 3 mois.
5. 🔗 SOURCES : URLs consultées."""

model = genai.GenerativeModel(
    model_name='gemini-2.0-flash', 
    system_instruction=instructions
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
        with st.spinner("Analyse stratégique en cours..."):
            try:
                today = datetime.now().strftime("%d %B %Y")
                prompt = f"Analyse {target} au {today}. Focus : {focus}."
                
                response = model.generate_content(prompt)
                
                if response.text:
                    st.markdown(response.text)
                    st.success("Analyse terminée.")
                else:
                    st.error("L'IA n'a pas renvoyé de texte.")
            except Exception as e:
                st.error(f"Erreur technique : {e}")
                st.info("Note : Si l'erreur 404 persiste, remplace 'gemini-2.0-flash' par 'gemini-3-flash-preview' dans le code.")
    else:
        st.info("Modifiez les paramètres à gauche et lancez l'analyse.")
