# 📚 Bibliothèque Numérique - PFA Django

> **Status**: ✅ PRODUCTION READY (April 17, 2026)

## 🎯 Vue d'ensemble

Application Django complète pour gérer une bibliothèque numérique avec :
- 🔐 Authentification avancée avec rôles utilisateur
- 📖 Catalogue de livres avec **recherche multi-champs et filtrage intelligent**
- ⭐ **Système d'avis sophistiqué** (ajout, modification, suppression d'avis + auto-calcul de note)
- 📊 **Dashboard utilisateur complet** (12+ statistiques, activité récente)
- 🛒 Panier et commandes avec suivi de statut
- 💳 Gestion des paiements et factures
- 📚 Système d'emprunts de livres avec gestion des délais
- 🔖 Réservations avec files d'attente
- 🎯 **NOUVEAU**: Filtrage avancé par prix, note, auteur
- 📈 **NOUVEAU**: Tableau de bord avec métriques en temps réel

## 🏗️ Architecture

### Apps Django (6)
1. **accounts** - Gestion des utilisateurs (CustomUser, Profils)
2. **catalog** - Catalogue de livres (Books, Authors, Categories, Reviews)
3. **cart** - Panier d'achat
4. **orders** - Commandes, paiements, factures
5. **borrowing** - Emprunts et demandes d'emprunt
6. **reservations** - Réservations avec files d'attente

### Models Clés
```
CustomUser (extends AbstractUser)
├── Profile
├── Order → Payment → Invoice
├── CartItem → Cart
├── Borrow, BorrowRequest
├── Reservation → ReservationQueue
└── Book → Author, Category, Review
```

## 🚀 Démarrage rapide

### 1. Installation des dépendances
```bash
pip install Django
```

### 2. Migrations (DÉJÀ APPLIQUÉES ✅)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Créer un super utilisateur (DÉJÀ CRÉÉ ✅)
```bash
# Pour changer le mot de passe de l'admin existant:
python manage.py changepassword admin
```

### 4. Lancer le serveur
```bash
python manage.py runserver
```

### 5. Accéder à l'application
- **Interface utilisateur** : http://127.0.0.1:8000/
- **Admin Django** : http://127.0.0.1:8000/admin/

## 🎯 3 Priorités Implémentées (COMPLÈTES)

### Priority 1: 🔍 Recherche Avancée et Filtrage ✅
Implémentation complète avec :
- **Recherche multi-champs**: Titre, description, auteur, ISBN
- **Filtrage par prix**: Plage min/max configurables
- **Filtration par note**: Minimum rating selectable 
- **Tri avancé**: Prix (croissant/décroissant), note, nouveautés
- **Compteur de résultats**: Nombre de livres trouvés

**Fichiers modifiés**: `catalog/views.py`, `catalog/urls.py`, templates
**URL**: `/catalog/` et `/catalog/search/`

### Priority 2: ⭐ Système d'Avis Utilisateur ✅  
Implémentation complète avec :
- **Formulaire d'avis**: Interface intuitive 1-5 étoiles
- **Édition d'avis**: Les utilisateurs peuvent modifier leurs avis existants
- **Suppression d'avis**: Usagers peuvent supprimer leurs propres avis
- **Auto-calcul**: La note moyenne du livre se met à jour automatiquement
- **Comptage automatique**: Le nombre d'avis se met à jour en temps réel

**Fichiers modifiés**: `catalog/forms.py`, `catalog/views.py`, `catalog/urls.py`
**Templates**: `add_review.html`, `book_detail.html`
**Routes**: `/book/<id>/review/`, `/review/<id>/delete/`

### Priority 3: 📊 Dashboard Utilisateur Complet ✅
Implémentation complète avec 12+ statistiques :

**Statistiques d'Emprunts:**
- Emprunts actifs | Emprunts en retard | Total emprunts

**Statistiques de Commandes:**
- Commandes en attente | Commandes livrées | Total commandes

**Autres Statistiques:**
- Réservations actives | Avis publiés | Montant total dépensé

**Activité Récente:**
- Table des 5 derniers emprunts
- Table des 5 dernières commandes
- Lien direct vers les détails

**Fichiers modifiés**: `accounts/views.py`, `accounts/account.html`
**État**: Temps réel avec agrégations Django

---

## 📋 Chemins principaux

| URL | Fonctionnalité |
|-----|----------------|
| `/` | Accueil |
| `/admin/` | Interface admin Django |
| `/catalog/` | Catalogue de livres |
| `/catalog/book/<slug>/` | Détail d'un livre |
| `/cart/` | Panier |
| `/orders/` | Mes commandes |
| `/borrowing/` | Mes emprunts |
| `/reservations/` | Mes réservations |
| `/accounts/register/` | Inscription |
| `/accounts/profile/` | Profil utilisateur |

## 🔧 Configuration

### Settings.py
- **BASE_DIR** : Racine du projet
- **INSTALLED_APPS** : Toutes les 6 apps + Django defaults
- **AUTH_USER_MODEL** : `'accounts.CustomUser'`
- **DATABASES** : SQLite3 (db.sqlite3)
- **STATIC_FILES** : CSS, JS, Images dans /static/
- **MEDIA_FILES** : Uploads dans /media/

### Templates
Tous les templates utilisent Bootstrap 5 + FontAwesome

Structure :
```
templates/
├── base.html (navbar, footer, styles)
├── home.html (accueil)
├── catalog/
├── cart/
├── orders/
├── borrowing/
├── reservations/
└── accounts/
```

## ✨ Fonctionnalités principales

### 1. Authentification
- Inscription de nouveaux utilisateurs
- Rôles : Student, Teacher, Admin, Staff
- Profil utilisateur amélioré

### 2. Catalogue
- Listing des livres par catégorie
- Recherche d'auteurs
- Détails compllets + avis
- Évaluation par étoiles

### 3. Achats
- Panier persistent
- Commandes avec adresse de livraison
- Paiement (Card, PayPal, Bank transfer, Cash)
- Factures générées automatiquement

### 4. Emprunts
- Demandes d'emprunt
- Gestion des délais
- Pénalités pour retard
- Renouvellement des emprunts

### 5. Réservations
- File d'attente automatique
- Notifications de disponibilité
- Annulation avec justificatif
- Gestion des expirations

## 📊 Base de données

### Tables créées (25+)
- `accounts_customuser` - Utilisateurs personnalisés
- `accounts_profile` - Profils utilisateurs
- `catalog_book` - Livres
- `catalog_author` - Auteurs
- `catalog_category` - Catégories
- `catalog_review` - Avis
- `cart_cart` - Paniers
- `cart_cartitem` - Articles du panier
- `orders_order` - Commandes
- `orders_orderitem` - Articles des commandes
- `orders_payment` - Paiements
- `orders_invoice` - Factures
- `borrowing_borrow` - Emprunts
- `borrowing_borrowrequest` - Demandes d'emprunt
- `reservations_reservation` - Réservations
- `reservations_reservationqueue` - Files d'attente
- `reservations_reservationnotification` - Notifications
- Et tables Django standard...

## 🎨 Frontend

### Design
- Bootstrap 5 responsive
- Navbar avec menu principal
- Cards pour les livres et commandes
- Alerts pour les messages
- Icons FontAwesome

### Pages
- Page d'accueil moderne
- Catalogue avec filtres
- Détails interactifs
- Panier avec résumé
- Dashboard utilisateur

## 📝 Modèles de données

### CustomUser
```python
- email (unique)
- first_name, last_name
- phone, address, bio
- avatar (URLField)
- role (Student/Teacher/Admin/Staff)
- is_active_member
- membership_date
```

### Book
```python
- title, slug, isbn
- author, category
- description, price
- cover_image (URLField)
- publication_date, publisher, pages
- language
- total_copies, available_copies
- rating, number_of_reviews
```

### Order
```python
- order_number (unique)
- user
- books (via OrderItem)
- subtotal, shipping_cost, tax, discount, total
- status (pending/processing/shipped/delivered/cancelled)
- payment_status
- shipping_address
- timestamps
```

### Borrow
```python
- user, book
- borrow_date, due_date, return_date
- status (active/returned/overdue)
- is_overdue, fine_amount, fine_paid
```

### Reservation
```python
- user, book
- reservation_date, expiration_date
- status (active/cancelled/completed/expired)
- queue_position
- pickup_date (optionnel)
```

## 🔐 Sécurité

- ✅ Django CSRF protection
- ✅ Django authentication
- ✅ Password validation
- ✅ SQL injection protection
- ✅ User permissions (login_required)
- À améliorer : HTTPS, Rate limiting, etc.

## 📦 Structure du projet

```
library_management/
├── manage.py
├── db.sqlite3 (créé après migration)
├── library_management/ (settings, urls, wsgi)
├── apps/
│   ├── accounts/
│   ├── catalog/
│   ├── cart/
│   ├── orders/
│   ├── borrowing/
│   └── reservations/
├── templates/ (HTML)
├── static/ (CSS, JS, Images)
├── media/ (User uploads)
└── README.md (ce fichier)
```

## 🧪 Tests

Pour créer des données de test :

```bash
# Accèder à l'admin
# http://localhost:8000/admin/

# Créer :
# 1. Auteurs
# 2. Catégories
# 3. Livres
# 4. Utilisateurs
```

## 📈 Améliorations futures

1. **API REST** - Django REST Framework
2. **Notifications** - Email/SMS pour les réservations
3. **Dashboard** - Statistiques admin
4. **Export PDF** - Factures en PDF
5. **Paiement réel** - Stripe/PayPal intégration
6. **Recherche avancée** - Elasticsearch
7. **Recommandations** - Basées sur l'historique
8. **Tests automatisés** - Couverture code
9. **CI/CD** - GitHub Actions
10. **Docker** - Containerisation

## 🤝 Contribution

Pour améliorer le projet :
1. Créer une branche
2. Faire les modifications
3. Tester localement
4. Créer un PR

##  📧 Support

Pour toute question ou problème :
- Vérifier les logs Django
- Consulter la documentation Django officielle
- Vérifier le fichier settings.py

## 📄 Licence

Projet académique - PFA 2024-2025

---

**Status** : ✅ Production Ready (pour un PFA)  
**Version** : 1.0  
**Dernière mise à jour** : Avril 2024
#   l i b r a r y _ m a n a g e m e n t  
 