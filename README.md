# 🚀 CY-HACKT — Cybersecurity Intelligence API

CY-HACKT est une API backend de veille en cybersécurité permettant de collecter, analyser et structurer automatiquement des informations issues de sources fiables (RSS, CISA KEV).

L’objectif est de fournir une base de données exploitable pour un dashboard ou des outils d’analyse.

---

## 🎯 Objectifs

- Collecter des données cybersécurité (RSS, CISA)
- Nettoyer et structurer les informations
- Analyser les menaces
- Scorer leur criticité
- Détecter les doublons
- Exposer une API REST exploitable

⚠️ L’IA n’est **pas encore intégrée volontairement** afin de garantir un backend stable et performant.

---

## 🧱 Stack technique

- **Backend** : FastAPI  
- **Base de données** : PostgreSQL  
- **Langage** : Python 3.13  

### Librairies principales

- `psycopg2`
- `FastAPI`
- `uvicorn`

---

## ⚙️ Architecture


app/
├── main.py
├── db.py
├── api/
├── core/
│ ├── config.py
│ └── logging.py
├── models/
│ └── article.py
├── services/
│ ├── article_service.py
│ ├── rss_service.py
│ ├── cisa_service.py
│ ├── scoring_service.py
│ ├── categorization_service.py
│ ├── cve_service.py
│ └── summary_service.py
├── utils/
│ ├── deduplicator.py
│ └── text_cleaner.py


---

## 🔄 Pipeline de traitement


Collecte (RSS + CISA)
→ Nettoyage texte
→ Filtrage (qualité + date)
→ Scoring (mots-clés + CVE)
→ Catégorisation
→ Extraction CVE
→ Déduplication
→ Résumé simple
→ Stockage PostgreSQL
→ API REST


---

## ✅ Fonctionnalités implémentées

### 📥 Collecte
- RSS (TheHackersNews, BleepingComputer, GitHub Advisories)
- CISA KEV

### 🧹 Traitement
- Nettoyage HTML
- Normalisation des données
- Filtrage articles (qualité + date)

### 🧠 Analyse
- Scoring (1 → 5)
- Explication du score (`score_reason`)
- Catégorisation automatique
- Extraction CVE

### 🔁 Déduplication
- Hash basé sur contenu
- Protection contre doublons ingestion

### 🗄️ Base de données
- PostgreSQL
- Contrainte unique sur `link`
- Index optimisés (performance lecture)

### ⚡ Performance
- Batch insert PostgreSQL
- Optimisation requêtes

### 🌐 API REST

#### Endpoints principaux


/ingest
/reset
/cleanup
/stats
/articles
/latest
/critical
/top-threats
/search
/articles/category/{category}
/articles/cve/{cve}


---


## 🚀 Installation

### 1. Cloner le repo

```git clone https://github.com/ton-username/cy-hackt.git```
```cd cy-hackt/backend```

### 2. Créer un environnement virtuel

```python python3 -m venv venv```
```python source venv/bin/activate```

### 3. Installer les dépendances

```pip install -r requirements.txt```

## * 🗄️ Configuration base de données *

# Créer la base PostgreSQL :

```CREATE DATABASE cyhackt;```

## Configurer la connexion :

```DATABASE_URL=postgresql://postgres:password@localhost:5432/cyhackt```

# ⚡ Lancer l’API
uvicorn app.main:app --reload

# Accès API
http://127.0.0.1:8000

# Swagger
http://127.0.0.1:8000/docs

---

## * 🧪 Utilisation rapide *

# Ingestion des données

```GET /ingest```

# Articles récents

```GET /latest```

# Menaces critiques

```GET /critical```

# Recherche

```GET /search?q=ransomware```

📈 État du projet
✅ Backend stable
✅ Pipeline fonctionnel
✅ Batch insert PostgreSQL
✅ Index base de données
✅ API exploitable

👉 Niveau actuel : MVP avancé prêt pour montée en charge

🔜 Roadmap
 * Recherche avancée (PostgreSQL full-text)
 * Scheduler automatique
 * Amélioration qualité des données
 * Optimisation API pour frontend
 * Refactor architecture scalable
 * Intégration IA (résumé, scoring avancé)
🧠 Vision

# CY-HACKT vise à devenir une plateforme complète de veille cybersécurité :

* Agrégation multi-sources
* Priorisation intelligente
* Dashboard interactif
* Analyse assistée par IA

# 👨‍💻 Auteur

### Lelio Plaine
