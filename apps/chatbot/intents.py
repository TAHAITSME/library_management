"""Base de connaissances conversationnelle du chatbot BiblioNUM.

Ce module reste volontairement simple: il decrit les intentions, les
formulations attendues, les reponses et les suggestions sans dependance Django.
La logique metier et les liens restent dans services.py.
"""

DEFAULT_SUGGESTIONS = [
    'Chercher un livre',
    'Réserver un livre',
    'Mes emprunts',
    'Paiement',
    'Réclamation',
]

VAGUE_PROBLEM_TERMS = (
    'probleme',
    'bug',
    'erreur',
    'ca ne marche pas',
    'ne fonctionne pas',
    'bloque',
    'impossible',
    'souci',
)

FOLLOW_UP_PATTERNS = {
    'reservation': {
        'unavailable': (
            'pas disponible',
            'indisponible',
            'plus disponible',
            'rupture',
            'pas en stock',
            'file attente',
        ),
        'after': ('apres', 'ensuite', 'et apres', 'puis'),
        'cancel': ('annuler', 'supprimer', 'retirer'),
        'status': ('suivre', 'etat', 'statut', 'mes reservations'),
    },
    'payment': {
        'after': ('apres paiement', 'et apres', 'ensuite', 'une fois paye'),
        'failed': ('echoue', 'refuse', 'ne marche pas', 'impossible', 'erreur', 'probleme'),
        'invoice': ('facture', 'recu', 'justificatif'),
    },
    'borrow': {
        'late': ('retard', 'en retard', 'depasse', 'amende', 'penalite'),
        'after': ('apres', 'ensuite', 'et apres'),
        'status': ('actif', 'en cours', 'statut', 'suivre'),
    },
    'return': {
        'late': ('retard', 'en retard', 'amende', 'penalite'),
        'stock': ('stock', 'disponible', 'exemplaire'),
    },
    'order': {
        'after': ('apres', 'ensuite', 'et apres'),
        'status': ('statut', 'etat', 'suivre'),
        'failed': ('probleme', 'annule', 'echoue', 'bloque'),
    },
    'cart': {
        'after': ('apres', 'valider', 'commander', 'payer'),
        'remove': ('supprimer', 'retirer', 'vider'),
    },
    'account': {
        'password': ('mot de passe', 'oublie', 'reset', 'changer'),
        'profile': ('profil', 'modifier', 'email', 'avatar'),
    },
}

CLARIFICATIONS = {
    'problem': {
        'answer': (
            "Je peux vous aider. Le problème concerne plutôt un livre, une réservation, "
            "un emprunt, une commande, un paiement, le panier ou votre compte ?"
        ),
        'suggestions': ['Chercher un livre', 'Réserver un livre', 'Paiement', 'Panier', 'Réclamation'],
    },
    'broken': {
        'answer': (
            "D'accord. Pouvez-vous préciser ce qui ne marche pas : la recherche de livre, "
            "la réservation, le paiement, la connexion ou le panier ?"
        ),
        'suggestions': ['Recherche de livre', 'Réservation', 'Paiement', 'Connexion', 'Panier'],
    },
    'short': {
        'answer': (
            "Je n'ai pas assez d'information pour répondre correctement. Vous pouvez me dire "
            "si vous voulez chercher un livre, réserver, emprunter, payer ou envoyer une réclamation ?"
        ),
        'suggestions': DEFAULT_SUGGESTIONS,
    },
    'unknown': {
        'answer': (
            "Je n'ai pas bien compris votre demande, mais je peux vous aider avec la recherche "
            "d'un livre, une réservation, un emprunt, une commande, un paiement ou une réclamation. "
            "Pouvez-vous préciser ce que vous voulez faire ?"
        ),
        'suggestions': DEFAULT_SUGGESTIONS,
    },
}

INTENT_KNOWLEDGE = {
    'greeting': {
        'keywords': ('bonjour', 'salut', 'slt', 'salam', 'hello', 'bonsoir', 'hi', 'hey'),
        'phrases': ('slt', 'salam cv', 'bonjour assistant', 'salut biblionum'),
        'answer': (
            "Bonjour, je suis l'assistant BiblioNUM. Je peux vous aider a chercher un livre, "
            "reserver un ouvrage, suivre vos emprunts, gerer vos commandes ou comprendre le paiement."
        ),
        'suggestions': ['Catalogue', 'Chercher un livre', 'Reserver un livre', 'Paiement'],
    },
    'help': {
        'keywords': ('aide', 'perdu', 'commencer', 'quoi faire', 'tu peux', 'guide', 'comment utiliser', 'fonctionne', 'assistant', 'plateforme'),
        'phrases': ('que peux tu faire', 'aide moi', 'comment utiliser le site', 'je suis perdu', 'je ne sais pas par ou commencer', 'je ne sais pas par où commencer', 'explique moi la plateforme'),
        'answer': (
            "Pas de problème, je vais vous guider.\n\n"
            "Pour commencer avec BiblioNUM :\n"
            "1. Consultez le catalogue.\n"
            "2. Recherchez un livre par titre, auteur ou catégorie.\n"
            "3. Ouvrez la page du livre.\n"
            "4. Réservez, empruntez ou ajoutez au panier selon la disponibilité.\n"
            "5. Suivez vos commandes, emprunts et réservations depuis votre espace utilisateur.\n\n"
            "Vous voulez que je vous aide à chercher un livre, réserver un livre ou consulter vos emprunts ?"
        ),
        'suggestions': ['Catalogue', 'Chercher un livre', 'Réserver un livre', 'Mes emprunts', 'Paiement'],
    },
    'catalog': {
        'keywords': ('catalogue', 'liste livres', 'tous les livres', 'rayon', 'bibliotheque', 'ouvrages'),
        'phrases': ('ou est le catalogue', 'voir le catalogue', 'consulter les livres'),
        'answer': (
            "Le catalogue rassemble les livres disponibles dans BiblioNUM. Vous pouvez l'ouvrir, "
            "parcourir les ouvrages, filtrer par categorie ou auteur, puis entrer dans la page de detail "
            "d'un livre pour voir son stock, son prix, ses informations et les actions possibles."
        ),
        'suggestions': ['Chercher un livre', 'Livres disponibles', 'Detail d un livre', 'Categories'],
    },
    'book_search': {
        'keywords': ('chercher', 'rechercher', 'trouver', 'titre', 'auteur', 'filtrer', 'mot cle', 'recherche'),
        'phrases': ('je cherche un livre', 'trouver un livre', 'rechercher par titre', 'livre data science'),
        'answer': (
            "Pour chercher un livre, ouvrez le catalogue puis utilisez la barre de recherche ou les filtres. "
            "Vous pouvez chercher par titre, auteur, categorie, prix ou disponibilite. Vous pouvez aussi "
            "m'ecrire directement une demande comme: livres Finance disponibles moins de 200 DH."
        ),
        'suggestions': ['Livres disponibles', 'Livres pas chers', 'Top livres Data Science', 'Catalogue'],
    },
    'book_detail': {
        'keywords': ('detail', 'fiche', 'page du livre', 'information livre', 'description', 'isbn'),
        'phrases': ('voir detail livre', 'ouvrir fiche livre', 'informations sur un livre'),
        'answer': (
            "La page de detail d'un livre affiche le titre, l'auteur, la categorie, la description, le prix, "
            "la disponibilite et les actions possibles. C'est depuis cette page que vous pouvez ajouter au panier, "
            "emprunter ou reserver selon le statut du livre."
        ),
        'suggestions': ['Chercher un livre', 'Reserver un livre', 'Emprunter un livre'],
    },
    'reservation': {
        'keywords': ('reservation', 'reserver', 'reserve', 'garder', 'mettre en attente', 'file attente', 'place'),
        'phrases': ('comment reserver un livre', 'je veux reserver', 'garder un livre', 'faire une reservation', 'mettre un livre en attente'),
        'answer': (
            "Pour réserver un livre, ouvrez le catalogue, choisissez le livre souhaité, puis cliquez sur Réserver "
            "depuis sa page de détail. Une fois la réservation enregistrée, vous pouvez suivre son état dans Mes réservations. "
            "Si le livre n'est pas disponible, votre demande peut être placée en attente selon les règles de la bibliothèque."
        ),
        'suggestions': ['Mes réservations', 'Livre indisponible', 'Annuler une réservation', 'Catalogue'],
    },
    'borrow': {
        'keywords': ('emprunt', 'emprunter', 'prendre un livre', 'pret', 'louer', 'demande emprunt', '30 jours', 'amende', 'retard'),
        'phrases': ('je veux prendre un livre', 'comment emprunter', 'emprunter un ouvrage'),
        'answer': (
            "Vous pouvez emprunter un livre s'il est disponible. Commencez par le rechercher dans le catalogue, "
            "ouvrez sa page de detail, puis choisissez l'action d'emprunt. Dans BiblioNUM, l'emprunt peut demander "
            "un paiement de garantie ou de frais, puis vous pourrez suivre son statut dans Mes emprunts."
        ),
        'suggestions': ['Chercher un livre', 'Mes emprunts', 'Retard emprunt', 'Retourner un livre'],
    },
    'return': {
        'keywords': ('retour', 'retourner', 'rendre', 'remettre', 'livre rendu'),
        'phrases': ('comment retourner un livre', 'je veux rendre un livre', 'retour livre'),
        'answer': (
            "Pour retourner un livre, l'emprunt doit etre confirme comme retourne par l'administration. "
            "Une fois le retour traite, le statut de l'emprunt change et le stock du livre est mis a jour. "
            "Si la date prevue est depassee, une penalite peut etre appliquee selon les regles de la bibliotheque."
        ),
        'suggestions': ['Mes emprunts', 'Retard et amende', 'Stock apres retour'],
    },
    'cart': {
        'keywords': ('panier', 'caddie', 'ajouter panier', 'vider panier', 'retirer panier'),
        'phrases': ('ouvrir mon panier', 'ajouter au panier', 'valider panier'),
        'answer': (
            "Le panier sert a preparer une commande. Depuis la fiche d'un livre, ajoutez l'ouvrage au panier, "
            "puis ouvrez le panier pour verifier les quantites, retirer un article ou valider la commande."
        ),
        'suggestions': ['Panier', 'Passer commande', 'Paiement', 'Chercher un livre'],
    },
    'order': {
        'keywords': ('commande', 'mes commandes', 'achat', 'livraison', 'statut commande', 'suivi commande'),
        'phrases': ('mes commandes', 'suivre commande', 'passer une commande'),
        'answer': (
            "Une commande est creee a partir du panier. Apres validation, vous pouvez suivre son statut dans Mes commandes: "
            "en attente, payee, en preparation, expediee, livree, annulee ou echouee selon le parcours."
        ),
        'suggestions': ['Mes commandes', 'Panier', 'Paiement', 'Facture'],
    },
    'payment': {
        'keywords': ('paiement', 'payer', 'stripe', 'carte', 'transaction', 'checkout', 'payement'),
        'phrases': ('je veux payer', 'comment fonctionne le paiement', 'paiement stripe', 'payer ma commande', 'mon paiement ne marche pas'),
        'answer': (
            "Pour payer une commande, ouvrez votre panier ou la commande concernee, puis lancez le paiement Stripe. "
            "Si le paiement reussit, la commande est confirmee et son statut est mis a jour. Si le paiement echoue, "
            "verifiez vos informations de paiement puis relancez la tentative depuis Mes commandes."
        ),
        'suggestions': ['Mes commandes', 'Panier', 'Paiement echoue', 'Facture'],
    },
    'invoice': {
        'keywords': ('facture', 'recu', 'justificatif', 'invoice'),
        'phrases': ('ou trouver ma facture', 'telecharger facture', 'recu commande'),
        'answer': (
            "La facture est liee a une commande payee. Elle recapitule les articles, les montants et les informations "
            "de commande. Pour la retrouver, commencez par ouvrir Mes commandes puis consultez la commande concernee."
        ),
        'suggestions': ['Mes commandes', 'Paiement', 'Commande payee'],
    },
    'complaint': {
        'keywords': ('reclamation', 'plainte', 'signaler', 'probleme', 'ticket', 'message admin'),
        'phrases': ('envoyer une reclamation', 'faire une plainte', 'signaler un probleme'),
        'answer': (
            "Pour envoyer une reclamation, ouvrez la page Reclamations, choisissez la categorie du probleme, "
            "indiquez la priorite puis decrivez clairement la situation. Vous pourrez ensuite suivre son traitement "
            "et lire la reponse de l'administration."
        ),
        'suggestions': ['Reclamation', 'Probleme paiement', 'Probleme commande', 'Contact support'],
    },
    'account': {
        'keywords': ('compte', 'utilisateur', 'espace client', 'mon espace', 'profil', 'wishlist'),
        'phrases': ('mon compte', 'compte utilisateur', 'espace personnel'),
        'answer': (
            "Votre compte BiblioNUM permet de suivre vos commandes, emprunts, reservations, reclamations et favoris. "
            "Depuis le profil, vous pouvez consulter ou modifier vos informations selon les options disponibles."
        ),
        'suggestions': ['Connexion', 'Inscription', 'Profil', 'Mes commandes'],
    },
    'login': {
        'keywords': ('connexion', 'connecter', 'login', 'se connecter', 'identifiant'),
        'phrases': ('je veux me connecter', 'comment se connecter', 'connexion compte'),
        'answer': (
            "Pour vous connecter, ouvrez la page de connexion puis saisissez votre identifiant ou email et votre mot de passe. "
            "Une fois connecte, vous pourrez acceder a vos commandes, emprunts, reservations et reclamations."
        ),
        'suggestions': ['Connexion', 'Mot de passe oublie', 'Inscription'],
    },
    'register': {
        'keywords': ('inscription', 'inscrire', 'creer compte', 'nouveau compte', 'register'),
        'phrases': ('creer un compte', 'je veux m inscrire', 'nouveau utilisateur'),
        'answer': (
            "Pour creer un compte, ouvrez la page d'inscription, renseignez vos informations puis validez le formulaire. "
            "Votre compte vous permettra de commander, emprunter, reserver et suivre vos demandes."
        ),
        'suggestions': ['Inscription', 'Connexion', 'Compte utilisateur'],
    },
    'profile': {
        'keywords': ('profil', 'modifier profil', 'email', 'avatar', 'mot de passe oublie', 'password'),
        'phrases': ('modifier mon profil', 'changer mot de passe', 'mot de passe oublie'),
        'answer': (
            "Depuis votre profil, vous pouvez consulter vos informations personnelles et les modifier si l'option est disponible. "
            "Si vous avez oublie votre mot de passe, utilisez le lien de reinitialisation depuis la page de connexion."
        ),
        'suggestions': ['Profil', 'Connexion', 'Mot de passe oublie'],
    },
    'stock': {
        'keywords': ('stock', 'indisponible', 'disponible', 'rupture', 'exemplaire', 'quantite'),
        'phrases': ('livre indisponible', 'plus en stock', 'stock livre'),
        'answer': (
            "Le stock indique combien d'exemplaires peuvent encore etre commandes ou empruntes. Si un livre est indisponible, "
            "vous pouvez verifier plus tard ou utiliser la reservation si elle est proposee. Quand un retour est confirme, "
            "le stock peut augmenter."
        ),
        'suggestions': ['Livre indisponible', 'Reserver un livre', 'Catalogue'],
    },
    'history': {
        'keywords': ('historique', 'activite', 'suivi', 'dernier', 'mes derniers'),
        'phrases': ('voir mon historique', 'historique activites', 'mes derniers emprunts'),
        'answer': (
            "Votre historique se consulte depuis les sections personnelles: Mes commandes, Mes emprunts, Mes reservations "
            "et Mes reclamations. Chaque page permet de suivre les derniers statuts connus."
        ),
        'suggestions': ['Mes commandes', 'Mes emprunts', 'Mes reservations', 'Reclamation'],
    },
    'admin': {
        'keywords': ('admin', 'administrateur', 'dashboard', 'back office', 'gestion', 'tableau de bord'),
        'phrases': ('role administrateur', 'que fait admin', 'gestion du stock'),
        'answer': (
            "L'administrateur gere le backoffice BiblioNUM: livres, categories, auteurs, utilisateurs, stock, commandes, "
            "paiements, factures, emprunts, reservations et reclamations. Le tableau de bord sert aussi a suivre les indicateurs importants."
        ),
        'suggestions': ['Gestion du stock', 'Commandes et paiements', 'Reclamations'],
    },
    'contact': {
        'keywords': ('contact', 'support', 'assistance', 'aide humaine', 'contacter'),
        'phrases': ('contacter support', 'parler a administration', 'besoin assistance'),
        'answer': (
            "Pour contacter le support BiblioNUM, utilisez la page Reclamations depuis votre compte. "
            "Decrivez le probleme et l'administration pourra le suivre et vous repondre."
        ),
        'suggestions': ['Reclamation', 'Connexion', 'Probleme paiement', 'Probleme commande'],
    },
}
