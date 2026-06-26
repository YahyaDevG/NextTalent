import streamlit as st

def show_auth_interface():
    # Correction ici : unsafe_allow_html=True pour centrer le texte
    st.markdown("<h1 style='text-align: center;'>💼 NextTalent</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Plateforme Intelligente d'Optimisation du Recrutement</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Initialisation de notre mini base de données en session
    if "user_database" not in st.session_state:
        st.session_state.user_database = {
            "recruteur@test.com": {"password": "123", "name": "Yahya Errahmani", "role": "Recruteur (RH)"},
            "candidat@test.com": {"password": "123", "name": "Yahya Errahmani", "role": "Candidat"}
        }

    tab_login, tab_register = st.tabs(["🔑 Se connecter", "📝 S'inscrire"])

    # ------------------------------------------------------------------
    # 1. MODULE DE CONNEXION
    # ------------------------------------------------------------------
    with tab_login:
        st.subheader("Connexion")
        
        email_input = st.text_input("Adresse e-mail", key="login_email")
        password_input = st.text_input("Mot de passe", type="password", key="login_password")
        role_input = st.selectbox("Rôle attendu", ["Recruteur (RH)", "Candidat"], key="login_role")

        if st.button("Se connecter", use_container_width=True, type="primary"):
            # Vérification stricte de l'existence du compte
            if email_input in st.session_state.user_database:
                user_info = st.session_state.user_database[email_input]
                
                # Vérification du mot de passe et du rôle choisi
                if user_info["password"] == password_input and user_info["role"] == role_input:
                    st.success(f"Bienvenue, {user_info['name']} !")
                    
                    st.session_state.authenticated = True
                    st.session_state.user_role = role_input
                    st.session_state.username = user_info["name"]
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect ou rôle non correspondant pour ce compte.")
            else:
                st.error("❌ Cet e-mail n'est pas enregistré. Veuillez d'abord vous inscrire dans l'onglet 'S'inscrire'.")

    # ------------------------------------------------------------------
    # 2. MODULE D'INSCRIPTION
    # ------------------------------------------------------------------
    with tab_register:
        st.subheader("Création de compte")
        
        reg_name = st.text_input("Nom complet", key="reg_name")
        reg_email = st.text_input("Adresse e-mail", key="reg_email")
        reg_password = st.text_input("Mot de passe", type="password", key="reg_password")
        reg_role = st.radio("Votre profil :", ["Recruteur (RH)", "Candidat"], key="reg_role")

        if st.button("Créer mon compte", use_container_width=True):
            if not reg_name or not reg_email or not reg_password:
                st.warning("⚠️ Veuillez remplir tous les champs du formulaire.")
            elif reg_email in st.session_state.user_database:
                st.error("❌ Un compte avec cette adresse e-mail existe déjà.")
            else:
                # Stockage des données de l'inscrit
                st.session_state.user_database[reg_email] = {
                    "password": reg_password,
                    "name": reg_name,
                    "role": reg_role
                }
                st.success("🎉 Compte créé avec succès ! Vous pouvez maintenant basculer sur l'onglet 'Se connecter'.")