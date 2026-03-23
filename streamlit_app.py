import streamlit as st
import google.generativeai as genai

# Configuration de l'interface
st.set_page_config(page_title="Agent Veille 5five", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ Agent de Veille Marketing")

# Récupération de la clé API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("La clé API est manquante dans les Secrets Streamlit !")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Modèle sans options complexes pour tester la connexion
model = genai.GenerativeModel('gemini-1.5-flash')

# Champ de saisie
prompt = st.text_area("Que voulez-vous demander à l'agent ?", "Fais-moi un résumé des forces de la marque 5five.")

if st.button("Lancer l'analyse"):
    with st.spinner("L'IA réfléchit..."):
        try:
            response = model.generate_content(prompt)
            st.markdown("### 📝 Résultat de l'analyse")
            st.write(response.text)
            st.balloons() # Enfin les ballons !
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
