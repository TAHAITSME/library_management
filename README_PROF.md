# Projet PFA - Bibliotheque Numerique Django

## Description

Application web Django pour la gestion d'une bibliotheque numerique. Le projet couvre l'authentification, le catalogue de livres, le panier, les commandes, les paiements, les emprunts, les reservations, les notifications, le dashboard administrateur et un chatbot d'assistance.

## Fonctionnalites principales

- Authentification avec utilisateur personnalise et profils.
- Catalogue de livres avec categories, auteurs, recherche, filtres et avis.
- Panier d'achat et commandes avec suivi de statut.
- Paiements Stripe et generation de factures.
- Gestion des emprunts, retours, frais et retards.
- Reservations avec file d'attente et notifications.
- Dashboard d'administration pour utilisateurs, livres, commandes, emprunts, paiements et reclamations.
- Chatbot en mode local ou IA selon la configuration.

## Prerequis

- Python 3.12 ou plus recent.
- MySQL en local.
- Un environnement virtuel Python.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Créer un fichier `.env` a partir de `.env.example`, puis renseigner les variables MySQL :

```env
DEBUG=True
SECRET_KEY=change-me
DB_NAME=library_db
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Créer la base MySQL `library_db`, puis appliquer les migrations :

```bash
python manage.py migrate
```

Optionnel : ajouter des donnees de demonstration.

```bash
python add_sample_data.py
```

## Lancement

```bash
python manage.py runserver
```

URLs principales :

- Application : http://127.0.0.1:8000/
- Admin Django : http://127.0.0.1:8000/admin/
- Catalogue : http://127.0.0.1:8000/catalog/
- Dashboard : http://127.0.0.1:8000/dashboard/

## Verification

Les controles suivants ont ete executes avant preparation :

```bash
python manage.py check
python manage.py test --keepdb
```

Resultat : 37 tests executes avec succes.

## Remarques pour l'envoi

Le fichier `.env`, l'environnement virtuel `.venv`, les caches Python et les fichiers temporaires ne doivent pas etre envoyes. Le fichier `.env.example` est fourni pour montrer les variables necessaires sans partager de secrets.
