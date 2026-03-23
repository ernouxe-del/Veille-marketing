import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from tinydb import TinyDB, Query
import uuid

# --- 1. CONFIGURATION (Base validée) ---
st.set_page_config(page_title="Agent Veille Stratégique", page_icon="🕵️‍♂️", layout="wide")

# Personnalisation CSS (Look AI Studio)
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1c22; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .date-badge { background-color: #343541; padding: 5px 10px; border-radius: 10px; font-size: 0.8rem; color: #ccc; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES (Tinydb) ---
DB_DIR = "db"
if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
db = TinyDB(os.path.join(DB_DIR, 'historique_veille.json'))
Analysis = Query()

# --- 3. NOUVELLE LOGIQUE D'ANALYSE (SINCÉRITÉ RADICALE AVEC SOURCES) ---
def executer_analyse(target, focus):
    # Récupération de la clé API
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Récupération de l'historique pour comparaison
    past_analyses = db.search(Analysis.target == target)
    comp_context = ""
    if past_analyses:
        latest_past = sorted(past_analyses, key=lambda x: x['timestamp'], reverse=True)[0]
        comp_context = f"\n\nCONTEXTE HISTORIQUE DU SITE (Pour comparaison) : {latest_past['report_text'][:1500]}"

  # --- INSTRUCTIONS DE RIGUEUR ABSOLUE ---
    instructions = f"""Tu es un Expert en Intelligence Stratégique. 
    Ta valeur ajoutée est la FIABILITÉ. Tu préfères donner MOINS d'informations que des informations fausses.

    CONSIGNES DE VÉRIFICATION :
    - CLICK & COLLECT : N'en parle JAMAIS, sauf si tu trouves un bouton ou une mention explicite "Retrait en magasin" ou "Click & Collect" sur le site actuel. Si absent, ignore totalement ce sujet.
    - RSE / ÉCO-RESPONSABILITÉ : N'en parle JAMAIS par défaut. Ne mentionne ce point que si une page "Engagement", "RSE" ou un label spécifique est visible. Ne pas inventer de valeurs éthiques générales.
    - PRODUITS OBSOLÈTES : Ne parle que des produits actuellement affichés dans les catégories du site {target}. Si un produit n'a pas de prix ou de bouton "Ajouter au panier", il est considéré comme indisponible.

    STRUCTURE DU RAPPORT (À n'afficher que si les données existent) :

    1. 📌 HIGHLIGHTS FR : 3 faits réels et vérifiables avec lien source.
    
    2. 💻 DIGITAL STOREFRONT & MERCHANDISING : 
       - Analyse de la Home Page et des bannières actuelles.
       - Focus sur les UNIVERS produits mis en avant.
       - Preuve (Lien URL) : [Insérer lien]

    3. 🏆 TOP 5 PRODUITS (ACTUELS & EN STOCK) :
       - Nom, Prix exact en €, et Lien direct vers la fiche produit (OBLIGATOIRE).
       - Si tu ne trouves pas 5 produits avec des liens valides, n'en liste que 3 ou 4.

    4. 🔄 ANALYSE COMPARATIVE : Évolutions réelles détectées.{comp_context if comp_context else ""}

    5. 🌿 ENGAGEMENTS & SERVICES (Optionnel) : 
       - À REMPLIR UNIQUEMENT si des preuves de RSE ou de services type Click & Collect sont trouvées. Sinon, supprimer cette section.
       - Preuve (Lien URL) : [Insérer lien]

    6. 🔗 RÉCAPITULATIF DES SOURCES."""

    try:
        model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=instructions)
        # On demande une analyse factuelle pour la date d'aujourd'hui
        response = model.generate_content(f"Analyse e-commerce rigoureuse de {target} au {datetime.now()}. Focus : {focus}.")
        return response.text
    except Exception as e:
        return f"Erreur technique lors de la génération : {e}"

# --- 4. SIDEBAR (Base de données groupée) ---
with st.sidebar:
    st.title("🕵️‍♂️ Mes Veilles")
    if st.button("➕ Nouvelle Analyse", type="primary"):
        st.session_state['selected_target'] = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏢 Marques suivies")
    
    # On récupère les marques uniques
    all_data = db.all()
    unique_targets = sorted(list(set([ana['target_name'] for ana in all_data])))
    
    for t_name in unique_targets:
        cols = st.columns([0.8, 0.2])
        if cols[0].button(f"🏢 {t_name}", key=f"target_{t_name}"):
            st.session_state['selected_target'] = t_name
            st.rerun()
        # Suppression de toute la marque et son historique
        if cols[1].button("🗑️", key=f"del_all_{t_name}"):
            db.remove(Analysis.target_name == t_name)
            st.session_state['selected_target'] = None
            st.rerun()

# --- 5. CORPS PRINCIPAL ---
selected_target = st.session_state.get('selected_target')

if selected_target is None:
    st.header("Nouvelle Analyse Stratégique")
    col1, col2 = st.columns([1, 1])
    target_input = col1.text_input("URL ou Marque à surveiller :", "https://www.5five.com/fr/")
    focus_input = col2.selectbox("Focus de l'analyse :", ["Global", "Prix", "Design", "Innovation"])
    
    if st.button("Lancer la veille"):
        with st.spinner("Analyse initiale et vérification des sources en cours..."):
            try:
                report_text = executer_analyse(target_input, focus_input)
                
                if "Erreur technique" in report_text:
                    st.error(report_text)
                else:
                    t_name = target_input.split("//")[-1].split("/")[0] if "http" in target_input else target_input
                    db.insert({
                        'id': str(uuid.uuid4()),
                        'target': target_input,
                        'target_name': t_name,
                        'timestamp': datetime.now().timestamp(),
                        'report_text': report_text,
                        'focus': focus_input
                    })
                    st.session_state['selected_target'] = t_name
                    st.rerun()
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
else:
    # AFFICHAGE DE LA TIMELINE POUR UNE MARQUE
    reports = sorted(db.search(Analysis.target_name == selected_target), key=lambda x: x['timestamp'], reverse=True)
    
    col_t, col_up = st.columns([0.7, 0.3])
    col_t.header(f"Veille : {selected_target}")
    
    if col_up.button("🔄 Actualiser (Nouvelle version)"):
        with st.spinner("Analyse approfondie des changements stratégiques..."):
            new_text = executer_analyse(reports[0]['target'], reports[0]['focus'])
            
            if "Erreur technique" in new_text:
                st.error(new_text)
            else:
                db.insert({
                    'id': str(uuid.uuid4()),
                    'target': reports[0]['target'],
                    'target_name': selected_target,
                    'timestamp': datetime.now().timestamp(),
                    'report_text': new_text,
                    'focus': reports[0]['focus']
                })
                st.rerun()

    st.markdown("---")

    # Affichage du rapport le plus récent
    st.subheader("📍 Dernière Analyse Factuelle")
    st.info(f"Établie le {datetime.fromtimestamp(reports[0]['timestamp']).strftime('%d/%m/%Y à %H:%M')}")
    st.markdown(reports[0]['report_text'])
    
    # Affichage des archives en dessous
    if len(reports) > 1:
        st.markdown("---")
        st.subheader("📜 Archives de cette marque")
        for i, old_ana in enumerate(reports[1:]):
            with st.expander(f"Version du {datetime.fromtimestamp(old_ana['timestamp']).strftime('%d/%m/%Y')}"):
                st.markdown(old_ana['report_text'])

    if st.button("⬅️ Retour"):
        st.session_state['selected_target'] = None
        st.rerun()
