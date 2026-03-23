import streamlit as st
import google.generativeai as genai

# Configuration de l'interface pro
st.set_page_config(page_title="Agent Veille 5five", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Agent d'Intelligence Stratégique : 5five & Co")
st.markdown("---")

# Connexion à l'IA avec ta clé validée
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Utilisation du modèle confirmé par le diagnostic
# On utilise 'gemini-3-flash-preview' qui est dans ta liste
model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction="""Tu es un Expert en Marketing et Veille Stratégique. 
    Ta mission est d'analyser les tendances, les sites web et les produits.
    Tu dois fournir des rapports structurés : 
    1. Points forts de la marque/produit.
    2. Analyse de la cible client.
    3. Recommandations pour l'équipe marketing de 5five."""
)

# Interface utilisateur
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
                # Requête à l'IA
                prompt = f"Réalise une veille complète sur {target} avec un focus sur {focus}."
                response = model.generate_content(prompt)
                
                st.success("Analyse terminée !")
                st.markdown("### 📊 Rapport de Veille")
                st.markdown(response.text)
                st.balloons()
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
    else:
        st.info("Entrez une cible à gauche et cliquez sur le bouton pour générer le rapport.")

st.sidebar.markdown("---")
st.sidebar.write("⚡ Propulsé par Gemini 3 Flash")
