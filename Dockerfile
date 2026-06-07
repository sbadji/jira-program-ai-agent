# 1. Utiliser une version de Python officielle, légère et stable
FROM python:3.11-slim

# 2. Configurer les variables d'environnement indispensables pour Python dans Docker
# - PYTHONDONTWRITEBYTECODE: Évite la création de fichiers .pyc lourds et inutiles dans le conteneur
# - PYTHONUNBUFFERED: Force l'affichage des logs en temps réel dans le terminal (crucial pour le débug)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Définir le dossier de travail à l'intérieur du conteneur
WORKDIR /app

# 4. Installer les dépendances système minimales si nécessaire (comme curl pour les healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copier uniquement le fichier des dépendances pour maximiser la mise en cache de Docker
COPY requirements.txt /app/

# 6. Installer les packages Python sans stocker le cache de pip (allège l'image Docker)
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copier le reste du projet (le dossier src, ui, agent, data...) dans le conteneur
COPY . /app/

# 8. Indiquer à Docker que l'application va écouter sur le port standard de Streamlit (8501)
EXPOSE 8501

# 9. Configurer un Healthcheck pour s'assurer que le conteneur tourne bien en production
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 10. Lancer l'application en forçant Streamlit à s'exécuter correctement dans un conteneur
CMD ["python3", "-m", "streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]