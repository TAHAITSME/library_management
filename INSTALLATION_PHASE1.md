# 🚀 PHASE 1: Guide d'Installation des Améliorations

**Date**: 17 Avril 2026  
**Statut**: DÉVELOPPEMENT  
**Version**: v1.1.0-beta

---

## 📋 TABLE DES MATIÈRES
1. [Prérequis](#prérequis)
2. [Installation Celery + Redis](#1-installation-celery--redis)
3. [Configuration Email](#2-configuration-email)
4. [Setup Recommandations](#3-setup-recommandations)
5. [Configuration Pagination](#4-configuration-pagination)
6. [Setup Codes Promo](#5-setup-codes-promo)
7. [Tester les Améliorations](#tester-les-améliorations)
8. [Dépannage](#dépannage)

---

## ✅ Prérequis

### Obligatoires
- ✅ Python 3.8+
- ✅ Django 6.0.3
- ✅ MySQL 5.7+
- ✅ (NOUVEAU) Redis 6.0+

### Installation Redis

#### Sur WINDOWS (recommandé via WSL2 ou Docker)

**Option 1: Docker (Facile)**
```bash
docker run --name redis -p 6379:6379 -d redis:latest
```

**Option 2: Installez directement sur Windows**
- Télécharger: https://github.com/microsoftarchive/redis/releases
- Ou via Chocolatey: `choco install redis`

**Option 3: WSL2**
```bash
wsl
sudo apt-get install redis-server
redis-server
```

Vérifier que Redis fonctionne:
```bash
redis-cli ping
# Réponse: PONG
```

---

## 1️⃣ Installation Celery + Redis

### Étape 1: Installer les dépendances

```bash
cd c:\library_management

# Installer celery et redis
pip install celery==5.3.4 redis==5.0.1 python-dotenv==1.0.0

# Ou utiliser requirements.txt
pip install -r requirements.txt
```

### Étape 2: Configuration affichée ✅

Les fichiers suivants ont été **DÉJÀ CRÉÉS**:
- ✅ `library_management/celery.py` - Configuration Celery
- ✅ `library_management/__init__.py` - Import Celery
- ✅ `library_management/settings.py` - Celery + Email config

### Étape 3: Vérifier les settings

```bash
python manage.py shell
>>> from celery import current_app
>>> print(current_app.conf.broker_url)
# Doit afficher: redis://localhost:6379
```

### Étape 4: Démarrer Celery Worker

Dans un **NOUVEAU TERMINAL**:

```bash
cd c:\library_management

# Démarrer Celery
celery -A library_management worker -l info

# Sur Windows, si erreur, utiliser:
celery -A library_management worker -l info -P solo
```

**Résultat attendu**:
```
[tasks]
  . accounts.tasks.send_welcome_email
  . accounts.tasks.send_password_reset_email
  . orders.tasks.send_order_confirmation_email
  . borrowing.tasks.send_borrow_confirmation_email
  [INFO] Worker ready
```

---

## 2️⃣ Configuration Email

### Étape 1: Obtenir les identifiants Gmail

1. Aller sur: https://myaccount.google.com/apppasswords
2. Sélectionner "Mail" et "Windows"
3. Copier le mot de passe généré (16 caractères)

### Étape 2: Configurer .env

Créer ou modifier `.env`:

```bash
# Copier depuis .env.example
cp .env.example .env

# Modifier .env avec vos identifiants:
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-16-caracteres
```

### Étape 3: Mettre à jour settings.py ✅

**DÉJÀ FAIT** dans `library_management/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your-email@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your-app-password')
DEFAULT_FROM_EMAIL = 'noreply@library.com'
```

### Étape 4: Tester Email

```bash
python manage.py shell

# Test d'envoi
from django.core.mail import send_mail

send_mail(
    'Test Sujet',
    'Test message',
    'noreply@library.com',
    ['votre-email@gmail.com'],
    fail_silently=False,
)

# Vérifier dans les logs Celery Worker
```

### Templates Email ✅

Créés automatiquement:
- ✅ `templates/emails/welcome.html`
- ✅ `templates/emails/order_confirmation.html`
- ✅ `templates/emails/borrow_reminder.html`

---

## 3️⃣ Setup Recommandations

### Fonctionnalité ✅ COMPLÈTE

**Views créées:**
- ✅ `get_user_recommendations()` - Algorithme
- ✅ `recommendations_view()` - Page publique
- ✅ `get_recommendations_context()` - Helper

**Routes:**
- ✅ `GET /catalog/recommendations/` - Page recommandations

**Template ✅:**
- ✅ `templates/catalog/recommendations.html`

### Tester les Recommandations

1. Visiter `/catalog/recommendations/`
2. Voir les livres recommandés basés sur l'historique
3. Voir les tendances du moment

### Algorithme Utilisé

```python
# 1. Livres des mêmes catégories que ceux empruntés
# 2. Livres les plus populaires (meilleure note)
# 3. Limiter à 9 résultats
```

---

## 4️⃣ Configuration Pagination

### Fonctionnalité ✅ COMPLÈTE

**Modifications:**
- ✅ `apps/catalog/views.py` - Paginator ajouté
- ✅ `templates/catalog/books_list.html` - UI pagination

**Paramètres:**
- 12 livres par page
- Navigation: Première, Précédente, Numéros, Suivante, Dernière

### Tester la Pagination

1. Aller à `/catalog/` 
2. Voir la pagination en bas
3. Cliquer sur les pages

---

## 5️⃣ Setup Codes Promo

### Model Coupon ✅ CRÉÉ

**Fonctionnalités:**
- ✅ Codes avec réductions (% ou €)
- ✅ Limites d'utilisation globales et par utilisateur
- ✅ Montants minimum / maximum
- ✅ Validité temporelle
- ✅ Utilisateurs spécifiques
- ✅ Livres applicables

### Étape 1: Créer Migration

```bash
python manage.py makemigrations orders

# Output: Creating migration orders/0004_coupon.py...
```

### Étape 2: Appliquer Migration

```bash
python manage.py migrate orders

# Output: Applying orders.0004_coupon... OK
```

### Étape 3: Admin Django

Accéder à `/admin/`:

1. Aller à "Codes promo"
2. Créer un nouveau coupon:
   - Code: `NOEL2026`
   - Type réduction: `Pourcentage %`
   - Valeur: `10`
   - Limite utilisation: `100`
   - Date début: Aujourd'hui
   - Date fin: 31/12/2026

### Exemple Code

```python
from apps.orders.models import Coupon

# Créer coupon
coupon = Coupon.objects.create(
    code='BIENVENUE',
    description='Bienvenue nouveau client',
    discount_type='percentage',
    discount_value=5,
    usage_limit=500,
    minimum_order_amount=20,
    start_date=timezone.now(),
    expiry_date=timezone.now() + timedelta(days=30),
)

# Utiliser dans commande
is_valid, msg = coupon.can_use_coupon(user, user_usage_count=0)
if is_valid:
    discount = coupon.apply_discount(100)  # 5€ pour 100€
    coupon.mark_as_used()
```

---

## 🧪 Tester les Améliorations

### Test 1: Email Bienvenue ✅

```bash
# 1. Créer nouvel utilisateur via `/accounts/register/`
# 2. Vérifier dans logs Celery Worker:
#    [INFO] Sent email to user@example.com
# 3. Vérifier inbox (peut être dans spam)
```

### Test 2: Recommandations ✅

```bash
# 1. Emprunter 2-3 livres
# 2. Aller à `/catalog/recommendations/`
# 3. Voir des livres des mêmes catégories
```

### Test 3: Pagination ✅

```bash
# 1. Aller à `/catalog/`
# 2. Scroller vers le bas
# 3. Cliquer sur page 2 / 3 / etc
```

### Test 4: Codes Promo ✅

```bash
# 1. Créer coupon via Admin
# 2. Dans cart, appliquer le code
# 3. Vérifier réduction appliquée
```

---

## 📁 Architecture des Changements

```
library_management/
├── library_management/
│   ├── celery.py                    ← NEW: Configuration Celery
│   ├── __init__.py                  ← MODIFIED: Import Celery
│   ├── settings.py                  ← MODIFIED: Celery + Email config
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   │   ├── tasks.py                 ← NEW: Email tasks
│   │   └── signals.py               ← MODIFIED: Déclencher emails
│   │
│   ├── catalog/
│   │   ├── views.py                 ← MODIFIED: Recommandations + Pagination
│   │   ├── urls.py                  ← MODIFIED: Route /recommendations/
│   │   └── models.py
│   │
│   ├── orders/
│   │   ├── models.py                ← NEW: Model Coupon
│   │   ├── admin.py                 ← MODIFIED: Admin Coupon
│   │   └── tasks.py                 ← NEW: Email orders tasks
│   │
│   └── borrowing/
│       ├── tasks.py                 ← NEW: Email borrowing tasks
│       └── views.py
│
├── templates/
│   ├── emails/                       ← NEW: Email templates
│   │   ├── welcome.html
│   │   ├── order_confirmation.html
│   │   └── borrow_reminder.html
│   │
│   └── catalog/
│       ├── recommendations.html      ← NEW: Recommandations page
│       └── books_list.html           ← MODIFIED: Pagination UI
│
├── .env.example                      ← NEW: Variables d'environnement
└── requirements.txt                  ← MODIFIED: Celery + Redis
```

---

## 🔧 Dépannage

### Erreur: "Connection refused" Redis

```bash
# Vérifier Redis est démarré
redis-cli ping
# Résultat attendu: PONG

# Si erreur, démarrer Redis
redis-server

# Ou sur Docker
docker start redis
```

### Erreur: Tasks non découvertes

```bash
# Vérifier que les tasks.py existent
# Celery recherche dans:
# - apps/accounts/tasks.py ✅
# - apps/orders/tasks.py ✅
# - apps/borrowing/tasks.py ✅

# Redémarrer Celery Worker
# (Ctrl+C puis relancer la commande)
```

### Erreur: Email non envoyé

```bash
# Vérifier configuration .env
# Vérifier identifiants Gmail
# Activer "Less secure apps": https://myaccount.google.com/lesssecureapps

# Test direct:
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Message', 'from@gmail.com', ['to@gmail.com'])
```

### Erreur: Migrations

```bash
# Générer migrations
python manage.py makemigrations

# Appliquer migrations  
python manage.py migrate

# Vérifier status
python manage.py showmigrations
```

---

## ✨ Prochaines Étapes

### Phase 2 (Semaine 3-4):
- [ ] Tri avancé des avis
- [ ] Intégration Stripe paiement
- [ ] Graphiques admin
- [ ] Wishlist utilisateur

### Phase 3 (Mois 2-3):
- [ ] API REST
- [ ] Mobile app
- [ ] 2FA

---

## 📞 Support

Besoin d'aide?

1. Vérifier le dépannage ci-dessus
2. Lire les logs Django et Celery
3. Tester avec `python manage.py shell`

---

**Installation réussie!** 🎉

Commencez à tester les nouvelles features maintenant.
