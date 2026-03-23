import streamlit as st
import google.generativeai as genai

st.title("🕵️‍♂️ Testeur de Connexion Agent")

# 1. Vérification de la clé
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ La clé n'est pas détectée dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 2. Liste des cerveaux à tester (du plus récent au plus stable)
model_names = ['gemini-3-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
selected_model = None

if st.button("Vérifier ma clé et le modèle"):
    for name in model_names:
        try:
            test_model = genai.GenerativeModel(name)
            # On tente une micro-réponse
            response = test_model.generate_content("Dis 'OK'")
            if response:
                selected_model = name
                st.success(f"✅ Succès ! Ta clé fonctionne avec le modèle : {name}")
                st.balloons()
                break
        except Exception as e:
            st.warning(f"⚠️ Le modèle {name} n'est pas disponible pour ta clé.")

    if not selected_model:
        st.error("❌ Aucun modèle ne répond. Vérifie ton compte Google AI Studio.")
