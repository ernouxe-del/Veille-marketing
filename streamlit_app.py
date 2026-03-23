import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

# Personnalisation CSS pour coller au look de AI Studio
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1a1c22;
        padding-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
    }
    .analysis-item {
        padding: 10px;
        border-bottom: 1px solid #333;
        cursor: pointer;
        color: #ddd;
    }
    .analysis-item:hover {
        background-color: #2a2d35;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTION DE LA BASE DE DONNÉES (Historique) ---
# Dossier pour stocker la base de données
DB_DIR = "db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# Initialisation de l'état de session
if 'selected_analysis_id' not in st.session_state:
    st.session_state['selected_analysis_id'] = None # None = Nouvelle analyse
if 'last_report' not in st.session_state:
    st.session_state['last_report'] = None

# --- 3. BARRE LATÉRALE (Sidebar style AI Studio) ---
with st.sidebar:
    st.title("🕵️‍♂️ Agent Veille")
    st.markdown("---")
    
    # BOUTON : Nouvelle Analyse (en haut, comme Playground)
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_analysis_id'] = None
        st.session_state['last_report'] = None
        st.rerun()
        
    st.markdown("### 📝 Historique des rapports")
    
    # Chargement de l'historique (du plus récent au plus ancien)
    all_analysis = sorted(db.all(), key=lambda x: x['timestamp'], reverse=True)
    
    # Affichage de la liste des rapports précédents
    if not all_analysis:
        st.write("*Aucun historique pour le moment.*")
    else:
        for ana in all_analysis:
            # Création du label du rapport (Marque + Date)
            date_str = datetime.fromtimestamp(ana['timestamp']).strftime("%d/%m/%Y")
            label = f"📊 {ana['target_name']} - {date_str}"
            
            # Bouton pour charger ce rapport spécifique
            if st.button(label, key=ana['id']):
                st.session_state['selected_analysis_id'] = ana['id']
                st.session_state['last_report'] = ana['report_text']
                st.rerun()
                
    st.markdown("---")
    st.write("⚡ Propulsé par Gemini 3")

# --- 4. CORPS PRINCIPAL DE L'APPLICATION ---

# Détermination du mode : Nouvelle analyse ou Lecture de rapport
current_id = st.session_state['selected_analysis_id']

if current_id is None:
    # --- MODE 1 : NOUVELLE ANALYSE ---
    st.header("Paramètres")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        target = st.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
        focus = st.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    
    with col2:
        btn_analyze = st.button("Lancer la veille stratégique", type="secondary")
    
    st.markdown("---")
    
    # ZONE DE RÉSULTAT
    if btn_analyze:
        with st.spinner("Analyse et comparaison stratégique en cours..."):
            
            # A. Connexion sécurisée
            if "GOOGLE_API_KEY" not in st.secrets:
                st.error("Clé API manquante dans les Secrets Streamlit.")
                st.stop()
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            # B. Recherche d'historique pour comparaison
            # On cherche les rapports précédents pour CETTE cible spécifique
            old_reports = db.search(Analysis.target == target)
            previous_context = ""
            if old_reports:
                # On prend le rapport le plus récent pour comparer
                latest_old = sorted(old_reports, key=lambda x: x['timestamp'], reverse=True)[0]
                date_old = datetime.fromtimestamp(latest_old['timestamp']).strftime("%d %B %Y")
                previous_context = f"\n\nCONTEXTE HISTORIQUE : Lors de la dernière analyse du {date_old}, les produits phares étaient {latest_old['report_text'][:500]}... Surligne uniquement les changements majeurs ou nouvelles stratégies depuis cette date."

            # C. Instructions Système (Base Neutre France + Historique)
            instructions = f"""Tu es un Expert en Intelligence Économique spécialisé sur le MARCHÉ FRANÇAIS. 
Ta mission est d'analyser la cible de façon NEUTRE, FACTUELLE et COMPARATIVE.

DIRECTIVES :
- FOCUS FRANCE : Analyse uniquement les données, prix et tendances en FRANCE.
- COMPARAIISON : Si un contexte historique est fourni ci-dessous, tu DOIS comparer les données actuelles avec les anciennes et mettre en évidence les évolutions stratégiques (prix, nouveaux produits, changement d'identité).{previous_context}

STRUCTURE DU RAPPORT :
1. 📌 HIGHLIGHTS FR : Les 3 faits marquants de l'actualité en France.
2. 🏆 TOP 5 PRODUITS (FRANCE) : (Prix en €, Design, Distribution, Stratégie, Succès).
3. 🔄 ANALYSE COMPARATIVE : Surligne les différences clés par rapport au dernier rapport si contexte historique fourni.
4. 🎨 IDENTITÉ VISUELLE : Couleurs, Style, Slogan.
5. 🔗 SOURCES."""

            # D. Modèle Gemini 3
            try:
                model = genai.GenerativeModel(
                    model_name='gemini-3-flash-preview',
                    system_instruction=instructions
                )
                today = datetime.now().strftime("%d %B %Y")
                prompt = f"Réalise la veille stratégique neutre de {target} au {today}. Focus : {focus}."
                response = model.generate_content(prompt)
                
                # E. Stockage du rapport dans la base de données
                target_name = target.split("//")[-1].split("/")[0] if "http" in target else target
                
                db.insert({
                    'id': str(uuid.uuid4()),
                    'target': target,
                    'target_name': target_name,
                    'focus': focus,
                    'timestamp': datetime.now().timestamp(),
                    'report_text': response.text
                })
                
                # F. Affichage
                st.success("Analyse terminée et stockée dans l'historique !")
                st.markdown(response.text)
                st.balloons()
                
            except Exception as e:
                st.error(f"Erreur technique : {e}")

    else:
        st.info("Configurez les paramètres ci-dessus et cliquez pour lancer l'analyse.")

else:
    # --- MODE 2 : LECTURE DE RAPPORT (Chargé depuis l'historique) ---
    # Récupération des infos du rapport sélectionné
    ana = db.get(Analysis.id == current_id)
    date_str = datetime.fromtimestamp(ana['timestamp']).strftime("%d %B %Y à %H:%M")
    
    st.header(f"Rapport : {ana['target_name']}")
    st.write(f"*Analysé le {date_str} - Focus : {ana['focus']}*")
    st.markdown("---")
    st.markdown(ana['report_text'])
    
    # Bouton optionnel pour revenir à une nouvelle analyse
    if st.button("⬅️ Revenir à une nouvelle analyse"):
        st.session_state['selected_analysis_id'] = None
        st.session_state['last_report'] = None
        st.rerun()
