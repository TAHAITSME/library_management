# 🔐 Guide de Connexion & Authentification

## ✅ Statut: Authentification Opérationnelle

L'authentification Django est **entièrement fonctionnelle**. Voir le rapport de diagnostic ci-dessous.

## 👥 Comptes de Test Disponibles

### Utilisateurs Réguliers:
```
Username: john
Password: password123
Full Name: John Doe
Role: Étudiant

---

Username: jane  
Password: password123
Full Name: Jane Smith
Role: Étudiant

---

Username: bob
Password: password123
Full Name: Bob Johnson
Role: Étudiant
```

### Compte Administrateur:
```
Username: admin
Password: admin123
Admin Panel: http://127.0.0.1:8000/admin/
```

## 📊 Rapport de Diagnostic d'Authentification

### ✅ Utilisateurs Détectés (4 total):
- ✅ `admin` - admin@example.com - **ACTIF**
- ✅ `bob` - bob@example.com - **ACTIF**
- ✅ `jane` - jane@example.com - **ACTIF**
- ✅ `john` - john@example.com - **ACTIF**

### ✅ Tests d'Authentification:
- ✅ **john:password123** → Authentification réussie (John Doe)
- ✅ **jane:password123** → Authentification réussie (Jane Smith)
- ✅ **admin:admin123** → Authentification réussie (Admin)
- ❌ **john:wrongpassword** → Échec (attendu)

### ⚙️ Configuration Vérifiée:
- ✅ `SESSION_COOKIE_HTTPONLY: True` - Sessions sécurisées
- ✅ `SESSION_COOKIE_SAMESITE: Lax` - Protection CSRF
- ✅ `CSRF_COOKIE_HTTPONLY: True` - Cookies sécurisés
- ✅ `CSRF_COOKIE_SAMESITE: Lax` - Protection cross-site
- ✅ `DEBUG: True` - Mode développement
- ✅ `ALLOWED_HOSTS: ['localhost', '127.0.0.1']` - Hosts autorisés
- ✅ `AUTH_USER_MODEL: accounts.CustomUser` - Modèle d'utilisateur personnalisé

## 🔗 URLs de Connexion

**Page de Connexion:**
```
http://127.0.0.1:8000/accounts/login/
```

**Inscription:**
```
http://127.0.0.1:8000/accounts/register/
```

**Dashboard Utilisateur (après connexion):**
```
http://127.0.0.1:8000/accounts/
```

**Profil Utilisateur:**
```
http://127.0.0.1:8000/accounts/profile/
```

## 🔄 Flux de Connexion

1. Accédez à `http://127.0.0.1:8000/accounts/login/`
2. Entrez votre nom d'utilisateur (ex: `john`)
3. Entrez votre mot de passe (ex: `password123`)
4. Cliquez sur **"Se Connecter"**
5. Vous serez redirigé vers `/accounts/` (dashboard)

## ⚠️ Troubleshooting - En Cas de Problème

### Erreur: "Invalid username or password"
- Vérifiez que vous utilisez les **bons identifiants**
- Les noms d'utilisateurs sont sensibles à la casse
- Essayez avec les comptes de test listés ci-dessus

### Les sessions ne persistent pas
- Vérifiez que les cookies sont activés dans votre navigateur
- Effacez le cache et les cookies du site
- Relancez le serveur Django

### Erreur CSRF
- Rafraîchissez la page de login
- Videz le cache du navigateur
- Vérifiez que `http://127.0.0.1:8000` est dans `CSRF_TRUSTED_ORIGINS`

### Erreur 403 Forbidden
- Vérifiez que votre adresse IP est dans `ALLOWED_HOSTS`
- Actuellement autorisé: `localhost`, `127.0.0.1`

## 🛡️ Sécurité de l'Authentification

✅ Mots de passe hachés avec PBKDF2
✅ Cookies de session HttpOnly
✅ CSRF tokens requis pour POST
✅ SameSite cookies configurés (Lax)
✅ Sessions chronologiquement limitées (2 semaines)
✅ Authentification multi-modèles compatible

## 📝 Notes

- Les données de test ont été créées avec la commande: `python manage.py create_sample_data`
- Le diagnostic d'authentification peut être exécuté avec: `python manage.py test_auth`
- Django check passe avec 0 erreurs
- Serveur actif à: `http://127.0.0.1:8000/`

---

**Date:** 19 Avril 2026
**Statut:** ✅ OPÉRATIONNEL
**Problème de connexion:** 🔧 RÉSOLU
