import streamlit as st
import google.generativeai as genai

st.title("🕵️‍♂️ Diagnostic de ta Clé API")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ La clé n'est pas trouvée dans les Secrets Streamlit.")
else:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    st.info(f"Clé détectée (début) : {api_key[:8]}...")

    if st.button("Lister mes modèles autorisés"):
        try:
            # Cette commande demande à Google la liste réelle des modèles pour TA clé
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            
            if available_models:
                st.success("✅ Ta clé fonctionne ! Voici tes modèles :")
                for m in available_models:
                    st.write(f"- {m}")
                st.balloons()
            else:
                st.warning("⚠️ La clé est valide mais Google ne te donne accès à aucun modèle 'generateContent'.")
        except Exception as e:
            st.error(f"❌ Erreur de connexion avec cette clé : {e}")
