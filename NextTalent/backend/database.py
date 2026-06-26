from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./nexttalent.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CandidatModel(Base):
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    telephone = Column(String, nullable=True)
    hard_skills = Column(String, nullable=True)
    soft_skills = Column(String, nullable=True)
    annees_experience = Column(Float, default=0.0)
    dernier_poste = Column(String, nullable=True)
    langues = Column(String, nullable=True)

class OffreModel(Base):
    __tablename__ = "offres"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    hard_skills_requis = Column(String, nullable=True)  # Stocké sous forme de chaîne "Python, SQL, FastAPI"
    annees_experience_requises = Column(Float, default=0.0)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()