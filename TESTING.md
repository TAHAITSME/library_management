# 🧪 Guide de Test - Bibliothèque Numérique

## ✅ Pré-requis
- ✅ Migrations appliquées
- ✅ Super utilisateur créé
- ✅ Serveur lancé (http://localhost:8000/)

## 🔓 Accès Admin

### Login Admin
```
URL: http://localhost:8000/admin/
Username: admin
Email: admin@example.com
Password: [À définir avec : python manage.py changepassword admin]
```

### Créer des données de test via l'Admin

#### 1. Créer des Auteurs
1. Aller à `Auteurs` dans l'admin
2. Ajouter :
   - Victor Hugo
   - Jules Verne
   - Alexandre Dumas

#### 2. Créer des Catégories
1. Aller à `Catégories` dans l'admin
2. Ajouter :
   - Littérature classique
   - Science-fiction
   - Aventure
   - Romance

#### 3. Créer des Livres
1. Aller à `Livres` dans l'admin
2. Ajouter plusieurs livres avec :
   - Titre, ISBN, Auteur, Catégorie
   - Description, Prix
   - URL couverture (ex: https://covers.openlibrary.org/...)
   - Dates, Nombre de pages
   - Quantités disponibles

Exemples :
```
Livre 1 : Les Misérables
- Auteur : Victor Hugo
- Prix : 15.99€
- Copies : 5

Livre 2 : Vingt mille lieues sous les mers
- Auteur : Jules Verne
- Prix : 12.99€
- Copies : 3
```

#### 4. Créer des Utilisateurs de Test
1. Aller à `Utilisateurs` dans l'admin
2. Ajouter utilisateurs avec emails différents
3. Assigner différents rôles :
   - Student (étudiant classique)
   - Teacher (professeur)
   - Staff (personnel)

## 👤 Tests - Interface Utilisateur

### 1. Test : Inscription & Profil

**Scénario** :
1. Aller à http://localhost:8000/accounts/register/
2. S'inscrire avec :
   - Email: testuser@example.com
   - Prénom: John
   - Nom: Doe
   - Téléphone: +33612345678
   - Rôle: Student
   - Mot de passe: TestPass123!

**Résultat attendu** :
- ✅ Redirection vers le profil
- ✅ Affichage des infos utilisateur
- ✅ Profil vide au départ
- ✅ Possibilité d'éditer le profil

### 2. Test : Catalogue

**Scénario** :
1. Aller à http://localhost:8000/catalog/
2. Voir la lista des livres
3. Cliquer sur un livre pour voir les détails

**Résultat attendu** :
- ✅ Affichage de tous les livres créés
- ✅ Tri possible (récent, A-Z, prix)
- ✅ Filtres par catégorie
- ✅ Page de détail complète

### 3. Test : Ajouter au Panier

**Scénario** :
1. Depuis un détail de livre
2. Cliquer "Ajouter au panier"
3. Aller à http://localhost:8000/cart/

**Résultat attendu** :
- ✅ Livre ajouté au panier
- ✅ Quantité modifiable
- ✅ Total calculé correctement
- ✅ Badge du panier mis à jour

### 4. Test : Commande

**Scénario** :
1. Depuis le panier, cliquer "Procéder au paiement"
2. Entrer une adresse de livraison
3. Sélectionner méthode de paiement
4. Confirmer

**Résultat attendu** :
- ✅ Commande créée
- ✅ Numéro unique généré
- ✅ Status : pending paiement
- ✅ Facture créée automatiquement
- ✅ Visible dans mes commandes

### 5. Test : Emprunt

**Scénario** :
1. Depuis détail d'un livre, cliquer "Demander"
2. Vérifier, dans emprunts

**Résultat attendu** :
- ✅ Demande d'emprunt créée
- ✅ Status : pending
- ✅ Admin peut approuver
- ✅ Apparaît dans mes emprunts actifs

### 6. Test : Réservation

**Scénario** :
1. Depuis détail livre avec few copies
2. Cliquer "Réserver"
3. Vérifier dans réservations

**Résultat attendu** :
- ✅ Réservation créée
- ✅ Position en file d'attente
- ✅ Expiration à 30 jours
- ✅ Visible dans mes réservations

## 🔧 Tests Admin

### 1. Gérer les Emprunts
1. Admin → Emprunts
2. Voir réservations en attente
3. Approuver/Rejeter
4. Créer manuellement un emprunt

**Actions** :
- ✅ Créer un emprunt direct
- ✅ Marquer comme retourné
- ✅ Calculer les pénalités
- ✅ Filtrer par statut

### 2. Gérer les Commandes
1. Admin → Commandes
2. Voir toutes les commandes
3. Modifier statut
4. Gérer paiements

**Actions** :
- ✅ Voir détails commande
- ✅ Changer statut (pending → processing → shipped → delivered)
- ✅ Voir facture
- ✅ Changer statut paiement

### 3. Gérer les Réservations
1. Admin → Réservations
2. Voir file d'attente
3. Marquer comme complétées

**Actions** :
- ✅ Voir position file d'attente
- ✅ Mettre à jour automatiquement
- ✅ Voir notifications envoyées

### 4. Gérer les Utilisateurs
1. Admin → Utilisateurs
2. Voir tous les utilisateurs
3. Éditer profils
4. Voir statistiques

**Actions** :
- ✅ Voir emprunts total
- ✅ Voir achats total
- ✅ Gérer rôle
- ✅ Activer/Désactiver compte

## 🐛 Problèmes courants & Solutions

| Problème | Solution |
|----------|----------|
| 404 Not Found sur `/` | Vérifier que urls.py a la route TemplateView vers home.html |
| Images ne s'affichent pas | Utiliser des URLs (pas ImageField) |
| Panier vide après login | Vérifier que Signal crée le Cart |
| Admin sans styles | Collectstatic : `python manage.py collectstatic` |
| Erreur ImageField | Vérifier que Pillow est installé |

## ✨ Cas de test avancés

### Test : Pénalité de retard
1. Créer un emprunt
2. Modifier due_date au passé
3. Retourner le livre
4. Vérifier que fine_amount est calculé

### Test : File d'attente des réservations
1. Create 3 livres avec 1 copie chacun
2. Créer 3 réservations pour le même livre
3. Vérifier positions (1, 2, 3)
4. Retourner le livre → Notification à position 1

### Test : Gestion des stocks
1. Vendre/Emprunter tous les livres
2. Vérifier que "Indisponible" s'affiche
3. Retourner un livre → Stock augmente

## 📊 Checklist de validation

- [ ] ✅ Utilisateurs peuvent s'inscrire
- [ ] ✅ Utilisateurs peuvent voir le catalogue
- [ ] ✅ Panier fonctionne
- [ ] ✅ Commandes créent factures
- [ ] ✅ Emprunts ont des pénalités
- [ ] ✅ Réservations ont files d'attente
- [ ] ✅ Admin peut gérer tout
- [ ] ✅ URLs toutes accessibles
- [ ] ✅ Pas d'erreurs sur console
- [ ] ✅ Base de données clean après migration

## 🎯 Résultat Final

Si tout fonctionne :
✅ **Application PFA Complète et Fonctionnelle**

---

**Notes** :
- Les tests peuvent être automatisés avec pytest + django
- Ajouter des fixtures pour les données de test
- Créer des views de test pour checker les redirections
