import streamlit as st

# ─── 1. Configuration de la page ─────────────────────────────────────────────
# Doit être la toute première commande Streamlit
st.set_page_config(
    page_title="NextTalent – AI Recruitment Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "mailto:support@nexttalent.io",
        "Report a bug": "mailto:bugs@nexttalent.io",
        "About": "**NextTalent** — Plateforme de recrutement augmentée par l'IA.",
    },
)

# ─── 2. CSS global ───────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Typographie & couleurs de base */
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* Masquer le menu hamburger natif et le footer Streamlit */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* Boutons primaires */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5, #7C3AED);
    border: none;
    color: white;
    border-radius: 8px;
    font-weight: 600;
    transition: opacity .2s;
}
div.stButton > button[kind="primary"]:hover { opacity: .88; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F8F7FF;
    border-right: 1px solid #E5E7EB;
}

/* Cards métriques */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 12px 16px;
}

/* Bandeau d'erreur custom */
.nt-error {
    background: #FEF2F2;
    border-left: 4px solid #EF4444;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    color: #991B1B;
    font-size: .9rem;
}

/* Badge de rôle dans le header */
.role-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 600;
    letter-spacing: .03em;
}
.role-recruiter { background: #DCFCE7; color: #166534; }
.role-candidate { background: #EEF2FF; color: #3730A3; }
</style>
""", unsafe_allow_html=True)

# ─── 3. Initialisation de la session ─────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False,
    "user_role":     None,
    "username":      "",
    "login_error":   "",
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── 4. Imports des modules métier ───────────────────────────────────────────
_import_errors: list[str] = []

try:
    from auth import show_auth_interface
except ImportError as e:
    _import_errors.append(f"**auth.py** — {e}")
    show_auth_interface = None  # type: ignore

try:
    from recruteur import show_recruiter_dashboard
except ImportError as e:
    _import_errors.append(f"**recruteur.py** — {e}")
    show_recruiter_dashboard = None  # type: ignore

try:
    from candidat import show_candidate_interface
except ImportError as e:
    _import_errors.append(f"**candidat.py** — {e}")
    show_candidate_interface = None  # type: ignore

# ─── 5. Alerte si des modules sont manquants ─────────────────────────────────
if _import_errors:
    st.markdown(
        "<div class='nt-error'>⚠️ <strong>Modules introuvables :</strong><br>"
        + "<br>".join(_import_errors)
        + "<br><small>Vérifiez que tous les fichiers sont dans le même dossier.</small></div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ─── 6. Routage principal ─────────────────────────────────────────────────────

def _role_badge(role: str) -> str:
    if role == "Recruteur (RH)":
        return f'<span class="role-badge role-recruiter">🏢 {role}</span>'
    return f'<span class="role-badge role-candidate">👤 {role}</span>'


if not st.session_state.authenticated:
    # ── Page non authentifiée ──
    show_auth_interface()

else:
    role = st.session_state.user_role

    # Bandeau de rôle discret en haut à droite
    col_title, col_role = st.columns([5, 1])
    with col_role:
        if role:
            st.markdown(_role_badge(role), unsafe_allow_html=True)

    # Dispatch par rôle
    if role == "Recruteur (RH)":
        if show_recruiter_dashboard:
            show_recruiter_dashboard()
        else:
            st.error("Le module recruteur n'a pas pu être chargé.")

    elif role in ("Candidat", "candidate", None):
        if show_candidate_interface:
            show_candidate_interface()
        else:
            st.error("Le module candidat n'a pas pu être chargé.")

    else:
        # Rôle inconnu — sécurité
        st.warning(f"Rôle non reconnu : `{role}`. Veuillez vous reconnecter.")
        if st.button("🔄 Revenir à la connexion"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()