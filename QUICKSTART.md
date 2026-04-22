# ⚡ Quick Start - Bibliothèque Numérique

## 🚀 Démarrer en 60 secondes

### 1️⃣ Vérifier que le serveur est lancé
```bash
# Le serveur devrait tourner sur http://localhost:8000/
# Si ce n'est pas le cas:
cd c:\library_management
python manage.py runserver 0.0.0.0:8000
```

### 2️⃣ Accéder à l'application
- **Site**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/

### 3️⃣ Se connecter en tant qu'Admin
```
Username: admin
Email: admin@example.com
```

⚠️ **Note**: Changer le mot de passe admin:
```bash
python manage.py changepassword admin
```

---

## 📊 Créer des données de test (Admin Panel)

### Étape 1: Ajouter des Auteurs
1. Aller à `/admin/catalog/author/`
2. Cliquer "Add Author"
3. Remplir les champs (au moins Prénom + Nom)
4. Répéter pour 3-5 auteurs

### Étape 2: Ajouter des Catégories
1. Aller à `/admin/catalog/category/`
2. Ajouter: Littérature, Science-fiction, Aventure, Romance, Jeunesse

### Étape 3: Ajouter des Livres
1. Aller à `/admin/catalog/book/`
2. Cliquer "Add Book"
3. Remplir le formulaire:
   - **Title**: (any)
   - **Slug**: (auto généré après save)
   - **ISBN**: (unique)
   - **Author**: Sélectionner de la liste
   - **Category**: Sélectionner de la liste
   - **Description**: (any)
   - **Price**: 10-30€
   - **Cover Image**: (URLField - exemple: https://via.placeholder.com/300x400)
   - **Publication Date**: (any)
   - **Publisher**: (any)
   - **Pages**: 100-500
   - **Language**: Français
   - **Total Copies**: 3-5
   - **Available Copies**: 3-5 (=Total)
   - **Status**: Available

**Conseil**: Créer minimum 5-10 livres pour un bon test

### Étape 4: Ajouter des Utilisateurs de Test
1. Aller à `/admin/accounts/customuser/`
2. Cliquer "Add User"
3. Créer 2-3 utilisateurs test:
   - testuser1@example.com / Student
   - testuser2@example.com / Teacher
   - testuser3@example.com / Student

---

## 🧪 Scénario de Test Complet

### Scénario 1: Achat Simple ✅
1. **Se déconnecter** de l'admin
2. **Aller à** http://localhost:8000/
3. **Cliquer** "Inscription"
4. **Créer un compte** avec vos infos
5. **Aller au Catalogue** et voir les livres
6. **Ajouter au panier** un ou plusieurs livres
7. **Valider** le panier
8. **Créer commande** avec adresse
9. **Payer** (choisir une méthode)
10. **Vérifier** dans "Mes Commandes"

### Scénario 2: Emprunter ✅
1. **Voir détails d'un livre**
2. **Cliquer "Demander"** (pour emprunter)
3. **Vérifier** dans "Mes Emprunts"
4. **Admin** peut approuver la demande

### Scénario 3: Réserver ✅
1. **Voir détails d'un livre** avec peu de copies
2. **Cliquer "Réserver"**
3. **Vérifier** dans "Mes Réservations"
4. Voir votre position en file d'attente

---

## 🎨 Personnaliser le Site

### Changer le nom de l'appli
1. Éditer `/templates/base.html`
2. Changer `"Bibliothèque"` par votre nom

### Changer les couleurs
1. Éditer `/templates/base.html`
2. Modifier les `:root { --primary-color: ... }`

### Ajouter votre logo
1. Éditer `/templates/base.html`
2. Remplacer l'icône `<i class="fas fa-book"></i>` par votre logo

### Ajouter du CSS custom
1. Créer `/static/css/custom.css`
2. Ajouter dans `/templates/base.html`:
   ```html
   <link rel="stylesheet" href="{% static 'css/custom.css' %}">
   ```

---

## 🔧 Commandes Django Utiles

### Reset de la base de données (ATTENTION: supprime tout!)
```bash
# Supprimer db.sqlite3
rm db.sqlite3

# Réappliquer les migrations
python manage.py migrate
python manage.py createsuperuser
```

### Voir les tables
```bash
python manage.py dbshell
.tables
.quit
```

### Créer un shell Python Django
```bash
python manage.py shell
>>> from apps.accounts.models import CustomUser
>>> CustomUser.objects.all()
```

### Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

---

## 📱 Responsive Design

L'application est **100% responsive**:
- ✅ Desktop (1440px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

Tester avec Firefox DevTools (F12) → Toggle device toolbar

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier que port 8000 est libre
netstat -ano | findstr :8000

# Tuer le processus (Windows)
taskkill /PID <PID> /F

# Ou utiliser un autre port
python manage.py runserver 0.0.0.0:8001
```

### Erreur "No module named 'django'"
```bash
pip install Django
```

### Erreur "TemplateDoesNotExist"
```bash
# Vérifier que templates/ existe
# Vérifier settings.py: TEMPLATES[0]['DIRS']
```

### Admin ne s'affiche pas bien
```bash
python manage.py collectstatic
```

---

## ✨ Points Clés à Présenter pour le PFA

1. **Architecture**: 6 apps Django bien sépaées
2. **Database**: Models normalisés avec relations complexes
3. **Frontend**: Bootstrap 5 responsive
4. **Fonctionnalités**: Toutes les étapes du cycle de vie d'une bibliothèque
5. **Admin**: Interface Django complète
6. **Security**: Django auth, CSRF protection

---

## 📚 Documentation

- [README.md](./README.md) - Vue d'ensemble complète
- [TESTING.md](./TESTING.md) - Guide de test détaillé
- [Django Docs](https://docs.djangoproject.com/) - Documentation officielle

---

## 🎯 Objectif Final

✅ Application fonctionnelle  
✅ Tous les CRUD implémentés  
✅ Interface utilisateur complète  
✅ Admin interface  
✅ Prête pour la présentation PFA  

**🚀 Bon courage avec votre PFA!**

---

Pour toute question, consulter:
1. Les logs Django (terminal)
2. La console du navigateur (F12)
3. L'admin panel (/admin/)
