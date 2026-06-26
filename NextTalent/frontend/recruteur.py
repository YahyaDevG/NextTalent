import streamlit as st
import pandas as pd

def show_recruiter_dashboard():
    # Barre latérale dédiée au recruteur
    with st.sidebar:
        st.markdown(f"### Espace Recruteur\n**{st.session_state.username}**")
        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True, key="btn_logout_rec"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.rerun()

    st.title("📊 Espace Recruteur - NextTalent")
    st.markdown("---")

    tab_analytics, tab_chatbot = st.tabs(["📊 Classement & Analytiques", "💬 Assistant IA (RAG)"])

    with tab_analytics:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.metric(label="Total Candidatures Reçues", value="42", delta="+5")
        col_kpi2.metric(label="Moyenne Score de Matching", value="74.5 %")
        col_kpi3.metric(label="Offres d'Emploi Actives", value="3")
        st.markdown("---")

        st.subheader("🔍 Recherche Avancée")
        score_min = st.slider("Score minimal (%)", 0, 100, 60)
        
        data = {
            "Candidat": ["Youssef El Amrani", "Anas Benjelloun", "Sara Chraibi"],
            "Score Sémantique": [92, 85, 78],
            "Compétences Détectées": ["Python, FastAPI, LLaMA 3.1", "Python, React", "FastAPI, SQL"]
        }
        df = pd.DataFrame(data)
        filtered_df = df[df["Score Sémantique"] >= score_min]

        col_table, col_chart = st.columns([3, 2])
        with col_table:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        with col_chart:
            st.bar_chart(filtered_df.set_index("Candidat")["Score Sémantique"])

    with tab_chatbot:
        st.subheader("💬 Assistant Virtuel de Recrutement")
        st.markdown("Interrogez votre base de CV en langage naturel (FAISS + LLaMA 3.1).")
        st.markdown("---")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Bonjour ! Je suis l'assistant NextTalent. Quel type de profil recherchez-vous aujourd'hui ?"}
            ]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if user_query := st.chat_input("Ex: Trouve-moi un expert Python..."):
            with st.chat_message("user"):
                st.write(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})

            with st.chat_message("assistant"):
                with st.spinner("Recherche FAISS & génération LLaMA 3.1..."):
                    import time
                    time.sleep(1.5)
                    response = f"**[Analyse LLaMA 3.1]** : Suite à votre recherche '{user_query}', le profil de Youssef El Amrani ressort comme le plus adapté avec un score de matching sémantique élevé."
                    st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})