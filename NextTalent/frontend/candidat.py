import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from PIL import Image
import time

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if len(name) >= 2 else name.upper()


def avatar_svg(initials: str) -> str:
    """Generate an SVG circle avatar with initials."""
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
      <circle cx="40" cy="40" r="40" fill="#4F46E5"/>
      <text x="40" y="46" text-anchor="middle" font-size="26"
            font-family="'Segoe UI', sans-serif" font-weight="700" fill="white">{initials}</text>
    </svg>
    """


def img_to_base64(pil_img) -> str:
    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ─── Session state defaults ────────────────────────────────────────────────────

def _init_state():
    """
    Complete session_state with missing values.
    - Never overrides keys already set by app.py (authenticated, username, etc.)
    - Pre-fills prenom/nom from st.session_state.username if profile is still empty
    """
    if "profile_photo" not in st.session_state:
        st.session_state.profile_photo = None

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "apply"

    # profile was created empty by app.py; pre-fill with the logged-in username
    # only if first load (prenom and nom still blank)
    profile = st.session_state.get("profile", {})
    if not isinstance(profile, dict):
        profile = {}

    if not profile.get("prenom") and not profile.get("nom"):
        username = st.session_state.get("username", "")
        parts    = username.strip().split()
        prenom   = parts[0]             if parts       else ""
        nom      = " ".join(parts[1:])  if len(parts) > 1 else ""
        profile.update({
            "prenom":         prenom,
            "nom":            nom,
            "email":          "",
            "telephone":      "",
            "localisation":   "",
            "poste_souhaite": "",
            "competences":    "",
            "bio":            "",
        })
        st.session_state.profile = profile

_init_state()


# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Sidebar card */
.profile-card {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    color: white;
    margin-bottom: 8px;
}
.profile-card h3 { margin: 10px 0 2px 0; font-size: 1rem; }
.profile-card p  { margin: 0; font-size: 0.8rem; opacity: 0.85; }
.profile-card img {
    border-radius: 50%;
    width: 80px; height: 80px;
    object-fit: cover;
    border: 3px solid rgba(255,255,255,0.6);
}

/* Greeting banner */
.greeting-banner {
    background: linear-gradient(90deg, #EEF2FF 0%, #F5F3FF 100%);
    border-left: 4px solid #4F46E5;
    border-radius: 0 12px 12px 0;
    padding: 14px 20px;
    margin-bottom: 20px;
}
.greeting-banner h2 { margin: 0 0 4px 0; color: #3730A3; font-size: 1.4rem; }
.greeting-banner p  { margin: 0; color: #6B7280; font-size: 0.9rem; }

/* Job card */
.job-card {
    border: 1.5px solid #E5E7EB;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    transition: border-color .2s;
    background: white;
}
.job-card:hover { border-color: #4F46E5; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def show_sidebar():
    with st.sidebar:
        username = st.session_state.username
        profile  = st.session_state.profile
        initials = get_initials(username)

        # Avatar
        if st.session_state.profile_photo is not None:
            b64 = img_to_base64(st.session_state.profile_photo)
            avatar_html = f'<img src="data:image/png;base64,{b64}" alt="avatar">'
        else:
            svg = avatar_svg(initials)
            b64 = base64.b64encode(svg.encode()).decode()
            avatar_html = f'<img src="data:image/svg+xml;base64,{b64}" alt="avatar">'

        poste = profile.get("poste_souhaite", "Candidat")
        st.markdown(f"""
        <div class="profile-card">
            {avatar_html}
            <h3>{username}</h3>
            <p>{poste}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        nav_options = {
            "🚀 Postuler":            "apply",
            "📂 Mes Candidatures":    "status",
            "👤 Mon Profil":          "profile",
        }
        for label, key in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.active_tab = key

        st.markdown("---")

        if st.button("🚪 Se déconnecter", use_container_width=True, key="btn_logout_cand"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.rerun()


# ─── Greeting banner ──────────────────────────────────────────────────────────

def show_greeting():
    prenom = st.session_state.profile.get("prenom", st.session_state.username.split()[0])
    poste  = st.session_state.profile.get("poste_souhaite", "")
    st.markdown(f"""
    <div class="greeting-banner">
        <h2>👋 Bonjour, {prenom} !</h2>
        <p>Bienvenue sur votre espace NextTalent · {poste}</p>
    </div>
    """, unsafe_allow_html=True)


# ─── Tab: Postuler ────────────────────────────────────────────────────────────

def tab_apply():
    st.subheader("🚀 Nouvelle Candidature")

    offres = [
        ("Développeur Python Backend (FastAPI)", "CDI · Paris · 45-55k€"),
        ("Ingénieur IA / Machine Learning",      "CDI · Lyon · 50-65k€"),
        ("Développeur Fullstack React/Node",     "CDI · Remote · 40-50k€"),
    ]
    titres = [o[0] for o in offres]
    details = {o[0]: o[1] for o in offres}

    job_offer = st.selectbox("Sélectionnez l'offre :", titres)
    st.info(f"📍 **{job_offer}** · {details[job_offer]}")

    uploaded_file = st.file_uploader("Déposez votre CV (PDF)", type=["pdf"])
    cover_letter  = st.text_area("Lettre de motivation (optionnel)", height=120,
                                 placeholder="Décrivez brièvement votre motivation…")

    if st.button("📤 Soumettre ma candidature", type="primary", disabled=uploaded_file is None):
        with st.status("Traitement intelligent de votre profil…") as status:
            st.write("🔍 Extraction sémantique (pdfplumber)…"); time.sleep(1.2)
            st.write("🧠 Analyse NER par LLaMA 3.1…");          time.sleep(1.5)
            st.write("📊 Matching sémantique avec l'offre…");   time.sleep(0.8)
            status.update(label="Candidature soumise !", state="complete")
        st.success(f"✅ CV analysé et associé au poste : **{job_offer}**")
        st.balloons()


# ─── Tab: Mes Candidatures ────────────────────────────────────────────────────

def tab_status():
    st.subheader("📂 Historique des Candidatures")

    history_data = {
        "Date":          ["24/06/2026",             "10/05/2026"],
        "Poste":         ["Développeur Python Backend", "Stage Data Science"],
        "Statut":        ["🟡 En cours d'examen",    "🔴 Refusé"],
        "Score Initial": ["84 %",                    "62 %"],
    }
    df = pd.DataFrame(history_data)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Candidatures envoyées", len(df))
    col_b.metric("En cours",  sum("En cours" in s for s in df["Statut"]))
    col_c.metric("Refusées",  sum("Refusé"   in s for s in df["Statut"]))

    st.markdown("---")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ─── Tab: Mon Profil ──────────────────────────────────────────────────────────

def tab_profile():
    st.subheader("👤 Mon Profil")

    col_photo, col_info = st.columns([1, 3], gap="large")

    with col_photo:
        # Display current avatar
        if st.session_state.profile_photo is not None:
            st.image(st.session_state.profile_photo, width=140)
        else:
            initials = get_initials(st.session_state.username)
            svg = avatar_svg(initials)
            b64 = base64.b64encode(svg.encode()).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{b64}" '
                f'style="width:140px;height:140px;border-radius:50%;" alt="avatar">',
                unsafe_allow_html=True
            )
        st.markdown("<br>", unsafe_allow_html=True)
        new_photo = st.file_uploader("Changer la photo", type=["png", "jpg", "jpeg"],
                                     label_visibility="collapsed")
        if new_photo:
            img = Image.open(new_photo).convert("RGB")
            # Crop to square
            w, h = img.size
            side  = min(w, h)
            img   = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
            img   = img.resize((200, 200))
            st.session_state.profile_photo = img
            st.rerun()

    with col_info:
        p = st.session_state.profile
        with st.form("form_profil"):
            c1, c2 = st.columns(2)
            prenom     = c1.text_input("Prénom",       value=p["prenom"])
            nom        = c2.text_input("Nom",          value=p["nom"])
            email      = c1.text_input("Email",        value=p["email"])
            telephone  = c2.text_input("Téléphone",    value=p["telephone"])
            localisation = st.text_input("Localisation", value=p["localisation"])
            poste_souhaite = st.text_input("Poste recherché", value=p["poste_souhaite"])
            competences  = st.text_area("Compétences (séparées par des virgules)",
                                        value=p["competences"], height=80)
            bio = st.text_area("Bio / Présentation", value=p["bio"], height=100)

            submitted = st.form_submit_button("💾 Enregistrer les modifications", type="primary")
            if submitted:
                st.session_state.profile.update({
                    "prenom": prenom, "nom": nom,
                    "email": email,   "telephone": telephone,
                    "localisation": localisation,
                    "poste_souhaite": poste_souhaite,
                    "competences": competences,
                    "bio": bio,
                })
                st.session_state.username = f"{prenom} {nom}"
                st.success("✅ Profil mis à jour avec succès !")
                st.rerun()

    # Skills tags display
    st.markdown("---")
    st.markdown("**Vos compétences**")
    tags_html = " ".join(
        f'<span style="background:#EEF2FF;color:#3730A3;border-radius:20px;'
        f'padding:4px 12px;font-size:0.85rem;margin:3px;display:inline-block;">'
        f'{s.strip()}</span>'
        for s in st.session_state.profile["competences"].split(",") if s.strip()
    )
    st.markdown(tags_html, unsafe_allow_html=True)


# ─── Main ─────────────────────────────────────────────────────────────────────

def show_candidate_interface():
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "apply"

    show_sidebar()

    st.title("💼 Espace Candidat — NextTalent")
    show_greeting()
    st.markdown("---")

    tab = st.session_state.active_tab
    if tab == "apply":
        tab_apply()
    elif tab == "status":
        tab_status()
    elif tab == "profile":
        tab_profile()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    show_candidate_interface()