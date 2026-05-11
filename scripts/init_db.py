import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    if not DATABASE_URL:
        print("Erreur: DATABASE_URL n'est pas défini dans le fichier .env")
        return

    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        print(f"Connexion réussie à la base de données.")

        # Lire le fichier schema.sql
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql = f.read()

        # Exécuter le SQL
        print("Exécution du script schema.sql...")
        cur.execute(sql)
        print("Schéma initialisé avec succès !")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Une erreur est survenue lors de l'initialisation de la base de données : {e}")

if __name__ == "__main__":
    init_db()
