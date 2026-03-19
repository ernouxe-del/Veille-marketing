import streamlit as st
import google.generativeai as genai

# Look de l'appli
st.set_page_config(page_title="Spy Marketing 5five", page_icon="🚀")
st.title("🕵️‍♂️ Agent de Veille : 5five & Co")

# On récupère la clé en toute sécurité
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

# Configuration de l'agent avec les instructions que tu as reçues de AI Studio
instructions = """Tu es un Agent d'Intelligence Stratégique. 
Ta mission est d'analyser les sites web (comme 5five.com) et le web en temps réel.
Tu dois fournir : 
1. Les faits marquants (promos, changements de site).
2. Le Top 5 des produits avec Prix, Design et Stratégie Marketing.
3. Une analyse de l'esthétique visuelle.
Sois précis, professionnel et détecte le 'pourquoi' du succès des produits."""

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", # Version stable et puissante pour la veille
    system_instruction=instructions
)

# Interface pour ton équipe
st.sidebar.header("Paramètres")
target_url = st.sidebar.text_input("URL à surveiller", value="https://www.5five.com/fr/")

if st.button("Lancer la veille stratégique"):
    with st.spinner("L'agent fouille le web..."):
        # Le "tools=['google_search']" est ce qui permet à l'IA de sortir sur internet
        response = model.generate_content(
            f"Fais ton rapport de veille complet sur {target_url} à la date d'aujourd'hui.",
            tools=[{'google_search': {}}] 
        )
        st.markdown("### 📊 Rapport de Veille Stratégique")
        st.write(response.text)
        st.success("Veille terminée avec succès.")

st.info("Ce rapport sert de base comparative pour vos décisions marketing.")
