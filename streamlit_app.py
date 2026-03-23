import streamlit as st
import google.generativeai as genai

# Look de l'appli
st.set_page_config(page_title="Agent Veille Gemini 3", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ Agent de Veille : Spécial 5five")

# Connexion sécurisée
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets !")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Utilisation de la version Gemini 3 (la plus récente en 2026)
# Si 'gemini-3-flash' ne passe pas, on testera 'gemini-1.5-pro'
try:
    model = genai.GenerativeModel('gemini-3-flash')
except:
    model = genai.GenerativeModel('gemini-1.5-pro')

# Interface
target = st.text_input("Cible de veille :", "https://www.5five.com/fr/")

if st.button("Lancer l'analyse"):
    with st.spinner("Analyse en cours avec Gemini 3..."):
        try:
            # On demande une analyse simple pour valider la connexion
            response = model.generate_content(f"Fais un court résumé des points forts du site {target}")
            st.markdown("### 📊 Rapport Flash")
            st.write(response.text)
            st.balloons()
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
