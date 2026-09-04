"""
Script d'insertion de nouvelles offres d'emploi RH professionnelles dans la base de données SQLite.
"""
from backend.database import SessionLocal
from backend.models import Offre, AuditLog

def ajouter_offres():
    db = SessionLocal()
    try:
        nouvelles_offres = [
            Offre(
                titre="Développeur Senior Python / FastAPI & IA",
                description="Nous recherchons un développeur backend chevronné pour concevoir des microservices performants, intégrer des modèles d'IA et optimiser les bases de données SQL/NoSQL chez ArtiWeb Fès.",
                experience_min_annees=3,
                competences_obligatoires=["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Git"],
                competences_souhaitees=["Docker", "Redis", "LangChain", "PyTest", "CI/CD"],
                formation_exigee="Bac+5 / Master ou Diplôme d'Ingénieur en Informatique",
                statut="ACTIF"
            ),
            Offre(
                titre="Développeur Full Stack React & Node.js",
                description="Rejoignez notre équipe Web pour créer des interfaces utilisateurs modernes, réactives et fluides en React/TypeScript connectées à des API REST et GraphQL.",
                experience_min_annees=2,
                competences_obligatoires=["React", "JavaScript", "TypeScript", "Node.js", "HTML/CSS"],
                competences_souhaitees=["Next.js", "TailwindCSS", "Redux", "Jest", "REST API"],
                formation_exigee="Bac+3 / Licence ou Master en Développement Web",
                statut="ACTIF"
            ),
            Offre(
                titre="Ingénieur Data / IA & Machine Learning",
                description="Conception de pipelines d'ingestion de données, prétraitement, entraînement et déploiement de modèles d'apprentissage automatique (NLP, Vision, Scoring) pour nos clients grands comptes.",
                experience_min_annees=2,
                competences_obligatoires=["Python", "Scikit-Learn", "Pandas", "NLP", "SQL"],
                competences_souhaitees=["TensorFlow", "PyTorch", "MLflow", "Power BI", "Spark"],
                formation_exigee="Bac+5 en Data Science / Intelligence Artificielle",
                statut="ACTIF"
            ),
            Offre(
                titre="Designer UI/UX & Product Designer",
                description="Création de maquettes haute fidélité, de design systems et de prototypes interactifs. Réalisation de tests utilisateurs et optimisation de l'ergonomie applicative.",
                experience_min_annees=1,
                competences_obligatoires=["Figma", "Adobe XD", "Prototypage", "Design System", "CSS"],
                competences_souhaitees=["Framer", "User Research", "Motion Design", "Wireframing"],
                formation_exigee="Bac+3 / Diplôme en Design Graphique ou UI/UX",
                statut="ACTIF"
            ),
            Offre(
                titre="Ingénieur DevOps & Cloud AWS/Docker",
                description="Gestion de l'infrastructure Cloud, automatisation des déploiements (CI/CD), conteneurisation des applications et supervision de la sécurité informatique.",
                experience_min_annees=3,
                competences_obligatoires=["Docker", "Linux", "AWS", "Git", "CI/CD"],
                competences_souhaitees=["Kubernetes", "Terraform", "Ansible", "Nginx", "Prometheus"],
                formation_exigee="Bac+5 Diplôme d'Ingénieur Systèmes & Réseaux",
                statut="ACTIF"
            )
        ]

        for offre in nouvelles_offres:
            db.add(offre)
            db.flush()
            audit = AuditLog(
                action="OFFRE_CREEE",
                entite_type="Offre",
                entite_id=offre.id,
                utilisateur="Systeme (Script Init)",
                details=f"Offre ID #{offre.id} '{offre.titre}' créée."
            )
            db.add(audit)

        db.commit()
        print(f"[SUCCESS] {len(nouvelles_offres)} nouvelles offres RH créées avec succès !")
    except Exception as e:
        db.rollback()
        print(f"[ERREUR] Échec de la création des offres : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ajouter_offres()
