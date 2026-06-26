import os
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Importation des utilitaires de calcul mathématique et sémantique
from sentence_transformers import SentenceTransformer, util

# Importation de nos composants de base de données
from database import engine, Base, CandidatModel, OffreModel, get_db

# Charger la clé API depuis le fichier .env
load_dotenv()

# Créer automatiquement les tables SQLite au démarrage de l'application
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NextTalent - Moteur d'Extraction, Stockage, Ranking & RAG")

# Initialisation du client Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Erreur : La variable GROQ_API_KEY est manquante dans le fichier .env")

client = Groq(api_key=GROQ_API_KEY)

# Initialisation du modèle d'Embeddings
print("Chargement du modèle d'embeddings sémantiques...")
model_embed = SentenceTransformer("all-MiniLM-L6-v2")
print("Modèle chargé avec succès !")

# Structure de données pour le Candidat
class CVStructure(BaseModel):
    nom_complet: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    hard_skills: List[str] = []
    soft_skills: List[str] = []
    annees_experience: float = 0.0
    dernier_poste: Optional[str] = None
    langues: List[str] = []

# Structure de données pour l'Offre d'emploi
class OffreStructure(BaseModel):
    titre: str
    description: Optional[str] = None
    hard_skills_requis: List[str] = []
    annees_experience_requises: float = 0.0

# Structure de données pour la requête de l'Assistant Chat RAG
class ChatQuery(BaseModel):
    question: str


@app.post("/extract-cv/", response_model=CVStructure)
async def extract_cv_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")
    
    text_brut = ""
    try:
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                text_brut += page.extract_text() or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de lecture PDF : {str(e)}")
    
    if not text_brut.strip():
        raise HTTPException(status_code=400, detail="Le PDF est vide ou est une image scannée.")

    prompt_ner = f"""
    Tu es un expert en recrutement RH. Analyse le texte brut suivant extrait d'un CV et extrait les informations de manière structurée.
    Tu doivent impérativement répondre UNIQUEMENT sous la forme d'un objet JSON valide, respectant exactement la structure suivante :
    {{
        "nom_complet": "Chaîne de caractères ou null",
        "email": "Chaîne de caractères ou null",
        "telephone": "Chaîne de caractères ou null",
        "hard_skills": ["liste", "de", "compétences", "techniques"],
        "soft_skills": ["liste", "de", "compétences", "comportementales"],
        "annees_experience": Nombre décimal ou entier,
        "dernier_poste": "Intitulé du dernier poste occupé ou null",
        "langues": ["liste", "des", "langues", "parlées"]
    }}

    Règles strictes :
    - Ne saisis aucun texte avant ou après le bloc JSON.
    - Si une information est absente, mets `null` ou une liste vide `[]`.
    
    Texte du CV :
    \"\"\"{text_brut}\"\"\"
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Tu es un extracteur de données JSON strict."},
                {"role": "user", "content": prompt_ner}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result_json = json.loads(completion.choices[0].message.content)
        
        h_skills = result_json.get("hard_skills")
        s_skills = result_json.get("soft_skills")
        langs = result_json.get("langues")

        nouveau_candidat = CandidatModel(
            nom_complet=result_json.get("nom_complet"),
            email=result_json.get("email"),
            telephone=result_json.get("telephone"),
            hard_skills=", ".join(h_skills) if isinstance(h_skills, list) else "",
            soft_skills=", ".join(s_skills) if isinstance(s_skills, list) else "",
            annees_experience=float(result_json.get("annees_experience") or 0.0),
            dernier_poste=result_json.get("dernier_poste"),
            langues=", ".join(langs) if isinstance(langs, list) else ""
        )
        
        db.add(nouveau_candidat)
        db.commit()
        db.refresh(nouveau_candidat)

        return result_json

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement ou stockage : {str(e)}")

@app.post("/offres/", response_model=dict)
def creer_offre(offre: OffreStructure, db: Session = Depends(get_db)):
    nouvelle_offre = OffreModel(
        titre=offre.titre,
        description=offre.description,
        hard_skills_requis=", ".join(offre.hard_skills_requis),
        annees_experience_requises=offre.annees_experience_requises
    )
    db.add(nouvelle_offre)
    db.commit()
    db.refresh(nouvelle_offre)
    return {"message": "Offre creee avec succes", "offre_id": nouvelle_offre.id}

@app.get("/offres/{offre_id}/ranking/")
def rank_candidats(offre_id: int, db: Session = Depends(get_db)):
    offre = db.query(OffreModel).filter(OffreModel.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail="Offre introuvable")
        
    skills_requis = [s.strip().lower() for s in offre.hard_skills_requis.split(",") if s.strip()] if offre.hard_skills_requis else []
    
    texte_offre_complet = f"{offre.titre}. {offre.description or ''}. Compétences: {offre.hard_skills_requis or ''}"
    embedding_offre = model_embed.encode(texte_offre_complet, convert_to_tensor=True)
    
    candidats = db.query(CandidatModel).all()
    ranking = []
    
    for c in candidats:
        skills_candidat = [s.strip().lower() for s in c.hard_skills.split(",") if s.strip()] if c.hard_skills else []
        skills_communs = set(skills_requis).intersection(set(skills_candidat))
        score_heuristique = len(skills_communs) / len(skills_requis) if skills_requis else 0.0
        
        if c.annees_experience >= offre.annees_experience_requises:
            score_experience = 1.0
        else:
            score_experience = c.annees_experience / offre.annees_experience_requises if offre.annees_experience_requises > 0 else 1.0
            
        texte_candidat_complet = f"Poste: {c.dernier_poste or ''}. Compétences: {c.hard_skills or ''}"
        embedding_candidat = model_embed.encode(texte_candidat_complet, convert_to_tensor=True)
        
        score_cosinus = util.cos_sim(embedding_offre, embedding_candidat).item()
        score_semantique = max(0.0, score_cosinus)
        
        score_final = (score_semantique * 0.40) + (score_heuristique * 0.40) + (score_experience * 0.20)
        
        ranking.append({
            "id": c.id,
            "nom_complet": c.nom_complet,
            "email": c.email,
            "skills_communs_exacts": list(skills_communs),
            "score_semantique_pur": round(score_semantique * 100, 2),
            "score_final_hybride": round(score_final * 100, 2)
        })
        
    ranking.sort(key=lambda x: x["score_final_hybride"], reverse=True)
    return ranking


# ==========================================
# NOUVELLE BRIXUE : MODULE ASSISTANT CHAT RAG
# ==========================================

@app.post("/chat-rag/", response_model=dict)
def chat_with_cvs(query: ChatQuery, db: Session = Depends(get_db)):
    """Assistant RH Intelligent : Posez une question sur l'ensemble de votre vivier de candidats (RAG)"""
    candidats = db.query(CandidatModel).all()
    if not candidats:
        return {"reponse": "Aucun candidat n'est actuellement disponible dans la base de données."}
    
    # 1. Étape 'Retrieval' (Recherche) : Trouver les candidats pertinents pour la question
    embedding_question = model_embed.encode(query.question, convert_to_tensor=True)
    
    candidats_pertinents = []
    for c in candidats:
        texte_profil = f"Candidat: {c.nom_complet or 'Inconnu'}. Poste: {c.dernier_poste or 'Non spécifié'}. Compétences: {c.hard_skills or ''}. Expérience: {c.annees_experience} ans."
        embedding_profil = model_embed.encode(texte_profil, convert_to_tensor=True)
        
        similarite = util.cos_sim(embedding_question, embedding_profil).item()
        
        # On garde le candidat s'il a un minimum de sens par rapport à la question
        if similarite > 0.15:
            candidats_pertinents.append((similarite, texte_profil))
            
    # Trier les candidats du plus au moins pertinent et prendre les 3 meilleurs
    candidats_pertinents.sort(key=lambda x: x[0], reverse=True)
    top_candidats = candidats_pertinents[:3]
    
    # 2. Construction du Contexte pour le LLM
    contexte_rh = "\n".join([item[1] for item in top_candidats])
    
    if not contexte_rh.strip():
        contexte_rh = "Aucun profil correspondant précisément dans la base."

    # 3. Étape 'Generation' (Appel à Groq)
    prompt_assistant = f"""
    Tu es un assistant RH virtuel expert intégré au logiciel NextTalent. Ton but est de répondre précisément à la question du recruteur en t'appuyant UNIQUE_MENT sur le contexte des candidats fourni ci-dessous.
    
    Règles très strictes :
    - Sois professionnel, clair et synthétique.
    - Ne cite ou ne parle QUE des candidats présents dans le contexte.
    - Si aucun candidat du contexte ne correspond à la demande, dis-le poliment sans inventer de faux profils.
    
    Contexte des candidats disponibles :
    \"\"\"
    {contexte_rh}
    \"\"\"
    
    Question du recruteur : {query.question}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Tu es un conseiller en recrutement RH factuel et rigoureux."},
                {"role": "user", "content": prompt_assistant}
            ],
            temperature=0.4
        )
        
        reponse_ia = completion.choices[0].message.content
        return {"reponse": reponse_ia}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération par l'assistant IA : {str(e)}")