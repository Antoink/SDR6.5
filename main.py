import streamlit as st
from utils import load_data, local_css, SDR_RED
import profiling
import os

st.set_page_config(
    page_title="SDR Performance",
    layout="wide",
    initial_sidebar_state="collapsed", 
    page_icon="logo_sdr.png"
)

# MOT DE PASSE
def check_password():
    """Retourne True si le mot de passe est correct."""
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        sub_col1, sub_col2, sub_col3 = st.columns([1, 1, 1])
        with sub_col2:
            if os.path.exists("logo_sdr.png"):
                st.image("logo_sdr.png", width=150)
            else:
                st.title("SDR")
        
        st.markdown("<h3 style='text-align:center;'>ACCÈS RESTREINT</h3>", unsafe_allow_html=True)
        
        pwd = st.text_input("Mot de passe", type="password", label_visibility="collapsed", placeholder="Entrez le mot de passe...")
        
        st.markdown("""
            <div style='text-align:center; margin-top:20px; font-size:11px; color:#888; font-weight:bold; letter-spacing:0.5px; border-top:1px solid #eee; padding-top:15px;'>
                Antoine Kaczmarek - DEPARTEMENT PERFORMANCE - STADE DE REIMS
            </div>
        """, unsafe_allow_html=True)
        
        if pwd:
            if pwd == "SDR":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
                
    return False



if check_password():
    local_css()
    full_data = load_data()
    profiling.show_profiling_page(full_data)



# streamlit run main.py
# ou 
# python -m streamlit run main.py
