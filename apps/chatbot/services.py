import re
import unicodedata
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.db.models import Q
from django.urls import reverse

from apps.borrowing.models import Borrow, BorrowRequest
from apps.catalog.models import Author, Book, Category
from apps.orders.models import Order
from apps.reservations.models import Reservation

from .intents import CLARIFICATIONS, DEFAULT_SUGGESTIONS, FOLLOW_UP_PATTERNS, INTENT_KNOWLEDGE, VAGUE_PROBLEM_TERMS


class LibraryAssistant:
    """Assistant metier local avec comprehension tolerante et memoire de dialogue."""

    MAX_RESULTS = 5
    CONTEXT_KEY = 'chatbot_context'

    INTENTS = {
        name: tuple(data.get('keywords', ())) + tuple(data.get('phrases', ()))
        for name, data in INTENT_KNOWLEDGE.items()
    }

    BUSINESS_TOPICS = {
        'project': {
            'keywords': ('projet', 'application', 'plateforme', 'systeme', 'biblionum', 'bibliotheque', 'objectif', 'role du site'),
            'answer': (
                "BiblioNUM est une application de gestion de bibliotheque. Elle centralise le catalogue, les comptes clients, "
                "les paniers, les commandes, les paiements, les emprunts, les reservations, la wishlist et les reclamations. "
                "Son but est de simplifier le travail de la bibliotheque et de donner aux utilisateurs un acces rapide aux livres."
            ),
            'intent': 'admin',
        },
        'roles': {
            'keywords': ('acteur', 'acteurs', 'role', 'admin', 'administrateur', 'bibliothecaire', 'client', 'adherent', 'utilisateur'),
            'answer': (
                "Les principaux acteurs sont le client et l'administration. Le client cherche des livres, commande, emprunte, reserve, "
                "gere son compte et envoie des reclamations. L'administrateur gere les livres, auteurs, categories, stocks, commandes, "
                "paiements, emprunts, reservations et reclamations depuis le tableau de bord."
            ),
            'intent': 'help',
        },
        'stock': {
            'keywords': ('stock', 'exemplaire', 'exemplaires', 'quantite', 'disponible', 'indisponible', 'rupture'),
            'answer': (
                "Le stock indique le nombre d'exemplaires disponibles pour un livre. Quand une commande payee ou un emprunt valide est confirme, "
                "le stock diminue. Quand un livre emprunte est retourne, le stock augmente. Si aucun exemplaire n'est disponible, le livre peut devenir indisponible."
            ),
            'intent': 'stock',
        },
        'search': {
            'keywords': ('chercher livre', 'rechercher livre', 'filtrer', 'recherche avancee', 'trouver livre', 'catalogue'),
            'answer': (
                "La recherche permet de trouver un livre par titre, auteur, categorie, prix, disponibilite ou note. "
                "Tu peux ecrire naturellement: livres finance disponibles, livres moins de 200 DH, ou top livres data science."
            ),
            'intent': 'catalog',
        },
        'security': {
            'keywords': ('securite', 'secure', 'proteger', 'donnees', 'mot de passe', 'authentification', 'permission'),
            'answer': (
                "La securite repose sur l'authentification, la protection CSRF de Django, les permissions d'acces et la separation des espaces. "
                "Les pages personnelles demandent une connexion, et les fonctions d'administration sont reservees aux comptes autorises."
            ),
            'intent': 'complaint',
        },
        'dashboard': {
            'keywords': ('dashboard', 'tableau de bord', 'administration', 'back office', 'gestion admin'),
            'answer': (
                "Le tableau de bord sert a piloter la bibliotheque: gestion des livres, auteurs, categories, utilisateurs, stocks, commandes, paiements, "
                "factures, emprunts, reservations et reclamations. Il donne aussi des indicateurs pour suivre l'activite."
            ),
            'intent': 'help',
        },
        'wishlist': {
            'keywords': ('wishlist', 'favori', 'favoris', 'liste souhait', 'souhaits'),
            'answer': (
                "La wishlist permet de garder des livres de cote sans les commander tout de suite. Depuis le catalogue ou la fiche livre, "
                "l'utilisateur peut ajouter un livre aux favoris puis le retrouver dans son espace personnel."
            ),
            'intent': 'account',
        },
        'complaint': {
            'keywords': ('reclamation', 'plainte', 'probleme', 'signaler', 'contact admin', 'message administration'),
            'answer': (
                "Une reclamation sert a signaler un probleme lie au compte, au paiement, a une commande, a un emprunt ou a une reservation. "
                "L'utilisateur choisit une categorie, une priorite, ecrit son message, puis l'administration peut suivre et repondre."
            ),
            'intent': 'account',
        },
        'invoice': {
            'keywords': ('facture', 'invoice', 'recu', 'justificatif'),
            'answer': (
                "La facture est liee a une commande payee. Elle reprend les informations de commande, le total et les donnees de facturation. "
                "L'administration peut la generer et l'utilisateur peut suivre ses commandes depuis son compte."
            ),
            'intent': 'invoice',
        },
        'delivery': {
            'keywords': ('livraison', 'livrer', 'expedition', 'expedie', 'adresse'),
            'answer': (
                "Pour une commande, l'utilisateur indique une adresse de livraison. Apres paiement confirme, la commande passe en preparation, "
                "puis peut etre marquee comme expediee et livree par l'administration."
            ),
            'intent': 'order',
        },
        'cancel': {
            'keywords': ('annuler', 'cancel', 'supprimer commande', 'annulation'),
            'answer': (
                "L'annulation depend de l'objet concerne. Une reservation active peut etre annulee. Une commande ne doit etre annulee que si son etat le permet, "
                "surtout avant traitement final. Pour un emprunt deja actif, on parle plutot de retour du livre."
            ),
            'intent': 'help',
        },
    }

    def __init__(self, user, session=None):
        self.user = user
        self.session = session
        self.context = dict(session.get(self.CONTEXT_KEY, {})) if session is not None else {}

    def answer(self, raw_message):
        self.message = raw_message.strip()
        self.normalized = self._normalize(self.message)
        self.tokens = re.findall(r'[a-z0-9]+', self.normalized)

        if self._is_too_short():
            return self._clarify()

        clarification = self._clarification_answer()
        if clarification:
            return clarification

        conversational = self._conversation_answer()
        if conversational:
            return conversational

        follow_up = self._follow_up_answer()
        if follow_up:
            return follow_up

        business = self._business_topic_answer()
        if business:
            return business

        intent = self._detect_intent()
        if intent == 'greeting':
            return self._remember('greeting', self._knowledge_answer('greeting'))
        if intent == 'help':
            return self._remember('help', self._knowledge_answer('help'))
        if intent in ('catalog', 'book_search', 'book_detail'):
            if intent == 'book_search' and (self._looks_like_precise_catalog_request() or self._is_catalog_follow_up_query()):
                return self._catalog_search()
            if intent == 'catalog' and self._looks_like_precise_catalog_request():
                return self._catalog_search()
            return self._remember(intent, self._knowledge_answer(intent))
        if intent == 'borrow':
            return self._remember('borrow', self._borrowing_answer())
        if intent == 'return':
            return self._remember('return', self._return_answer())
        if intent == 'cart':
            return self._remember('cart', self._cart_answer())
        if intent == 'payment':
            return self._remember('payment', self._payment_answer())
        if intent == 'order':
            return self._remember('order', self._orders_answer())
        if intent == 'invoice':
            return self._remember('invoice', self._invoice_answer())
        if intent == 'reservation':
            return self._remember('reservation', self._reservations_answer())
        if intent == 'account':
            return self._remember('account', self._account_answer())
        if intent == 'login':
            return self._remember('login', self._login_answer())
        if intent == 'register':
            return self._remember('register', self._register_answer())
        if intent == 'profile':
            return self._remember('profile', self._profile_answer())
        if intent == 'complaint':
            return self._remember('complaint', self._complaint_answer())
        if intent == 'contact':
            return self._remember('contact', self._contact_answer())
        if intent == 'admin':
            return self._remember('admin', self._admin_answer())
        if intent == 'stock':
            return self._remember('stock', self._stock_answer())
        if intent == 'history':
            return self._remember('history', self._history_answer())
        if intent == 'category':
            return self._remember('category', self._categories_answer())
        if intent == 'author':
            return self._remember('author', self._authors_answer())
        if intent == 'unknown':
            return self._unknown_answer()
        return self._catalog_search()

    def _is_catalog_follow_up_query(self):
        return bool(
            self.context.get('intent') == 'catalog'
            and (
                self._extract_price_range() != (None, None)
                or self._matches('moins', 'plus', 'disponible', 'dispo', 'stock', 'aussi', 'encore', 'autre')
            )
        )

    def _knowledge_answer(self, intent):
        data = INTENT_KNOWLEDGE.get(intent, INTENT_KNOWLEDGE['help'])
        return self._with_suggestions({
            'answer': data['answer'],
            'results': [],
            'actions': self._actions_for_intent(intent),
        }, intent)

    def _clarification_answer(self):
        if self._matches('ca ne marche pas', 'ne fonctionne pas', 'marche pas', 'bloque', 'impossible') and not self._has_domain_hint():
            return self._clarification('broken')
        if self._matches(*VAGUE_PROBLEM_TERMS) and not self._has_domain_hint():
            return self._clarification('problem')
        return None

    def _clarification(self, key):
        data = CLARIFICATIONS[key]
        response = {
            'answer': data['answer'],
            'results': [],
            'actions': self._common_actions(),
            'suggestions': data.get('suggestions', DEFAULT_SUGGESTIONS),
        }
        self._save_context('clarification', {'reason': key})
        return response

    def _has_domain_hint(self):
        domain_words = []
        for intent, data in INTENT_KNOWLEDGE.items():
            if intent in ('greeting', 'help', 'contact'):
                continue
            domain_words.extend(data.get('keywords', ()))
        return any(self._normalize(word) in self.normalized for word in domain_words)

    def _follow_up_answer(self):
        last_intent = self.context.get('intent')
        if not last_intent:
            return None
        if not self._looks_like_contextual_follow_up():
            return None

        if last_intent in ('reservation', 'stock') and self._follow_matches('reservation', 'unavailable'):
            return self._remember('reservation', self._with_suggestions({
                'answer': (
                    "Si le livre n'est pas disponible, votre reservation peut etre placee dans une file d'attente. "
                    "Vous gardez ainsi votre priorite et vous pourrez suivre l'etat depuis Mes reservations."
                ),
                'results': [],
                'actions': self._actions_for_intent('reservation'),
            }, 'reservation'))
        if last_intent == 'reservation' and self._follow_matches('reservation', 'cancel'):
            return self._remember('reservation', self._with_suggestions({
                'answer': (
                    "Pour annuler une reservation, ouvrez Mes reservations puis consultez la reservation concernee. "
                    "Si l'annulation est disponible pour son statut, utilisez l'action d'annulation affichee."
                ),
                'results': [],
                'actions': self._actions_for_intent('reservation'),
            }, 'reservation'))
        if last_intent == 'payment' and self._follow_matches('payment', 'after'):
            return self._remember('payment', self._with_suggestions({
                'answer': (
                    "Apres le paiement, la commande passe au statut paye ou en preparation, le stock est mis a jour "
                    "et une facture peut etre generee. Vous pouvez verifier tout cela depuis Mes commandes."
                ),
                'results': [],
                'actions': self._actions_for_intent('payment'),
            }, 'payment'))
        if last_intent == 'payment' and self._follow_matches('payment', 'failed'):
            return self._remember('payment', self._with_suggestions({
                'answer': (
                    "Si le paiement echoue, verifiez vos informations de carte, votre solde et relancez le paiement depuis la commande. "
                    "La commande peut rester en attente ou echouee tant que le paiement n'est pas confirme."
                ),
                'results': [],
                'actions': self._actions_for_intent('payment'),
            }, 'payment'))
        if last_intent in ('borrow', 'return') and (self._follow_matches('borrow', 'late') or self._follow_matches('return', 'late')):
            return self._remember('borrow', self._with_suggestions({
                'answer': (
                    "Si vous retournez un livre apres la date prevue, l'emprunt peut passer au statut en retard. "
                    "Une amende peut etre calculee selon les regles de la bibliotheque, puis le retour sera confirme apres traitement."
                ),
                'results': [],
                'actions': self._actions_for_intent('borrow'),
            }, 'borrow'))
        if last_intent == 'order' and self._follow_matches('order', 'status'):
            return self._remember('order', self._with_suggestions({
                'answer': (
                    "Le suivi se fait depuis Mes commandes. Vous y verrez si la commande est en attente, payee, "
                    "en preparation, expediee, livree, annulee ou echouee."
                ),
                'results': [],
                'actions': self._actions_for_intent('order'),
            }, 'order'))
        if last_intent == 'cart' and self._follow_matches('cart', 'after'):
            return self._remember('cart', self._with_suggestions({
                'answer': (
                    "Apres validation du panier, BiblioNUM cree une commande. Vous pouvez ensuite payer cette commande "
                    "et suivre son statut depuis Mes commandes."
                ),
                'results': [],
                'actions': self._actions_for_intent('cart'),
            }, 'cart'))
        return None

    def _looks_like_contextual_follow_up(self):
        return self._matches(
            'et si', 'et apres', 'apres', 'ensuite', 'puis', 'dans ce cas', 'si le livre',
            'si je suis', 'si ca', 'que faire', 'comment faire', 'pourquoi', 'quand'
        )

    def _follow_matches(self, intent, key):
        return any(self._normalize(item) in self.normalized for item in FOLLOW_UP_PATTERNS.get(intent, {}).get(key, ()))

    def _conversation_answer(self):
        if self._is_gibberish():
            return self._unknown_answer()
        if self._matches('bonjour', 'salam', 'salut', 'hello', 'bonsoir', 'hi', 'hey'):
            return self._with_suggestions({
                'answer': (
                    "Bonjour, je suis l'assistant BiblioNUM. Je peux vous aider a chercher un livre, "
                    "comprendre les reservations, suivre vos emprunts, gerer votre panier ou repondre aux questions de paiement."
                ),
                'results': [],
                'actions': self._common_actions(),
            }, 'help')
        if self._matches('ca va', 'cv', 'labas', 'labass', 'comment vas tu', 'comment tu vas'):
            return self._with_suggestions({
                'answer': "Ca va bien, merci. Pose-moi une question sur le catalogue, l'emprunt, la reservation, le paiement, ton compte ou l'administration.",
                'results': [],
                'actions': self._common_actions(),
            }, 'help')
        if self._matches('merci', 'thanks', 'thank you', 'parfait', 'super', 'ok', 'd accord', 'bien compris'):
            return self._with_suggestions({
                'answer': "Avec plaisir. Si tu veux, je peux aussi t'aider a trouver un livre par domaine, auteur ou prix.",
                'results': [],
                'actions': [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
            }, 'help')
        if self._matches('au revoir', 'aurevoir', 'bye', 'a bientot'):
            return self._with_suggestions({
                'answer': "A bientot. Tu peux rouvrir l'assistant quand tu as besoin d'aide sur BiblioNUM.",
                'results': [],
                'actions': [],
            }, 'help')
        if self._matches('qui es tu', 'tu es qui', 'c est quoi ce chatbot', 'ton role'):
            return self._with_suggestions({
                'answer': (
                    "Je suis l'assistant BiblioNUM. Mon role est de guider les clients dans la plateforme: "
                    "recherche de livres, disponibilite, panier, commandes, emprunts, reservations et compte utilisateur."
                ),
                'results': [],
                'actions': self._common_actions(),
            }, 'help')
        if self._matches('que puis je faire ici', 'qu est ce que je peux faire ici', 'comment utiliser le site'):
            return self._help()
        return None

    def _business_topic_answer(self):
        best_topic = None
        best_name = ''
        best_score = 0
        for name, topic in self.BUSINESS_TOPICS.items():
            score = self._topic_score(topic['keywords'])
            if score > best_score:
                best_topic = topic
                best_name = name
                best_score = score

        if not best_topic or best_score < 2:
            return None
        if best_name in ('stock', 'search') and self._looks_like_precise_catalog_request():
            return None

        return self._with_suggestions({
            'answer': best_topic['answer'],
            'results': [],
            'actions': self._actions_for_intent(best_topic['intent']),
        }, best_topic['intent'])

    def _topic_score(self, keywords):
        score = 0
        for keyword in keywords:
            normalized = self._normalize(keyword)
            if ' ' in normalized:
                if normalized in self.normalized:
                    score += 3
                continue
            if normalized in self.tokens:
                score += 2 if len(normalized) > 4 else 1
            elif len(normalized) > 5 and any(self._similar_token(token, normalized) for token in self.tokens):
                score += 1
        return score

    def _looks_like_precise_catalog_request(self):
        if not self._matches('livre', 'livres', 'bouquin', 'ouvrage'):
            return False
        return bool(
            self._find_category()
            or self._find_author()
            or self._extract_price_range() != (None, None)
            or self._matches('disponible', 'disponibles', 'dispo', 'stock', 'moins cher', 'top', 'meilleur')
        )

    def _help(self):
        return self._with_suggestions({
            'answer': (
                "Je peux t'aider a utiliser BiblioNUM: chercher un livre, filtrer par categorie, auteur ou prix, "
                "verifier la disponibilite, comprendre le panier, le paiement, les commandes, les emprunts et les reservations."
                "\nDis-moi par exemple: livres marketing moins de 200 DH, livres disponibles, ou comment reserver un livre."
            ),
            'results': [],
            'actions': self._common_actions(),
        }, 'help')

    def _cart_answer(self):
        return self._with_suggestions({
            'answer': (
                "Pour ajouter un livre au panier, ouvre la fiche du livre puis clique sur Ajouter au panier. "
                "Depuis le panier, tu peux modifier les quantites, supprimer un livre, vider le panier ou valider la commande."
            ),
            'results': [],
            'actions': [
                {'label': 'Ouvrir le panier', 'url': reverse('cart:cart')},
                {'label': 'Chercher un livre', 'url': reverse('catalog:books_list')},
            ],
        }, 'cart')

    def _payment_answer(self):
        return self._with_suggestions({
            'answer': (
                "Parcours paiement commande: ouvrez le panier, creez la commande, puis lancez le paiement Stripe. "
                "Apres validation, BiblioNUM confirme la commande et met a jour son etat. Si Stripe revient en annulation, "
                "relancez le paiement depuis la commande concernee."
            ),
            'results': [],
            'actions': [
                {'label': 'Ouvrir le panier', 'url': reverse('cart:cart')},
                {'label': 'Mes commandes', 'url': reverse('orders:orders_list')},
            ],
        }, 'payment')

    def _return_answer(self):
        return self._with_suggestions({
            'answer': (
                "Pour retourner un livre, l'emprunt doit etre traite par l'administration. Une fois le retour confirme, "
                "le stock du livre augmente et l'emprunt passe a l'etat retourne. En cas de retard, une penalite peut etre appliquee."
            ),
            'results': [],
            'actions': [
                {'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')},
                {'label': 'Catalogue', 'url': reverse('catalog:books_list')},
            ],
        }, 'return')

    def _borrowing_answer(self):
        if self._is_personal_question():
            if not self._is_authenticated():
                return self._login_required_answer('Connecte-toi pour voir tes emprunts, retards et demandes.')

            borrows = Borrow.objects.filter(user=self.user).select_related('book').order_by('-borrow_date')
            if self._matches('retard', 'depasse', 'amende'):
                borrows = borrows.filter(Q(status='overdue') | Q(is_overdue=True))
            if self._matches('actif', 'active', 'en cours'):
                borrows = borrows.filter(status='active')

            requests = BorrowRequest.objects.filter(user=self.user).select_related('book').order_by('-requested_date')[:3]
            visible_borrows = list(borrows[: self.MAX_RESULTS])
            total = borrows.count()

            if not visible_borrows and not requests:
                return self._with_suggestions({
                    'answer': "Je n'ai pas trouve d'emprunt ou de demande correspondant a ta question.",
                    'results': [],
                    'actions': [{'label': 'Chercher un livre', 'url': reverse('catalog:books_list')}],
                }, 'borrow')

            results = [self._borrow_result(borrow) for borrow in visible_borrows]
            results.extend(self._borrow_request_result(request) for request in requests)
            return self._with_suggestions({
                'answer': f"J'ai compris que tu veux suivre tes emprunts. J'ai trouve {total} emprunt(s) correspondant(s).",
                'results': results,
                'actions': [{'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')}],
            }, 'borrow')

        return self._with_suggestions({
            'answer': (
                "Pour emprunter un livre, choisissez un livre disponible depuis le catalogue, ouvrez sa fiche, puis lancez l'action d'emprunt. "
                "Parcours d'emprunt: 1. choisir un livre disponible, 2. payer 30% du prix du livre, "
                "3. Stripe confirme le paiement, 4. le stock diminue, 5. le livre doit etre rendu sous 30 jours. "
                "En cas de retard, le montant d'emprunt est double: les 30% initiaux + une amende du meme montant."
            ),
            'results': [],
            'actions': [{'label': 'Trouver un livre a emprunter', 'url': reverse('catalog:books_list')}, {'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')}],
        }, 'borrow')

    def _orders_answer(self):
        if self._is_personal_question():
            if not self._is_authenticated():
                return self._login_required_answer('Connecte-toi pour voir tes commandes et l etat de paiement.')

            orders = Order.objects.filter(user=self.user).order_by('-created_at')
            if self._matches('paye', 'payee', 'payees', 'valide'):
                orders = orders.filter(payment_status='paid')
            elif self._matches('attente', 'pending'):
                orders = orders.filter(payment_status='pending')
            elif self._matches('echoue', 'failed'):
                orders = orders.filter(payment_status='failed')

            total = orders.count()
            if total == 0:
                return self._with_suggestions({
                    'answer': "Je n'ai pas trouve de commande avec ce statut. Tu peux creer une commande depuis le panier.",
                    'results': [],
                    'actions': [{'label': 'Panier', 'url': reverse('cart:cart')}, {'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
                }, 'order')

            return self._with_suggestions({
                'answer': f"J'ai compris que tu veux suivre tes commandes. Voici {min(total, self.MAX_RESULTS)} resultat(s) sur {total}.",
                'results': [self._order_result(order) for order in orders[: self.MAX_RESULTS]],
                'actions': [{'label': 'Toutes mes commandes', 'url': reverse('orders:orders_list')}],
            }, 'order')

        return self._with_suggestions({
            'answer': (
                "Une commande regroupe les livres valides depuis le panier. Vous pouvez suivre son statut, son paiement "
                "et sa livraison depuis Mes commandes. Une commande en attente ou echouee peut etre payee a nouveau si elle n'est pas annulee."
            ),
            'results': [],
            'actions': [{'label': 'Panier', 'url': reverse('cart:cart')}, {'label': 'Mes commandes', 'url': reverse('orders:orders_list')}],
        }, 'order')

    def _invoice_answer(self):
        return self._with_suggestions({
            'answer': (
                "La facture est rattachee a une commande payee. Elle sert de justificatif avec les articles, le total et les informations de commande. "
                "Depuis votre espace, commencez par ouvrir Mes commandes pour retrouver la commande concernee."
            ),
            'results': [],
            'actions': [{'label': 'Mes commandes', 'url': reverse('orders:orders_list')}],
        }, 'invoice')

    def _reservations_answer(self):
        if self._is_personal_question():
            if not self._is_authenticated():
                return self._login_required_answer('Connecte-toi pour voir tes reservations.')

            reservations = Reservation.objects.filter(user=self.user).select_related('book').order_by('-reservation_date')
            if self._matches('active', 'actif', 'cours'):
                reservations = reservations.filter(status='active')
            elif self._matches('annule', 'cancel'):
                reservations = reservations.filter(status='cancelled')

            total = reservations.count()
            if total == 0:
                return self._with_suggestions({
                    'answer': "Je n'ai pas trouve de reservation correspondant a ta question.",
                    'results': [],
                    'actions': [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
                }, 'reservation')
            return self._with_suggestions({
                'answer': f"J'ai trouve {total} reservation(s). Je t'affiche les plus recentes.",
                'results': [self._reservation_result(reservation) for reservation in reservations[: self.MAX_RESULTS]],
                'actions': [{'label': 'Mes reservations', 'url': reverse('reservations:list')}],
            }, 'reservation')

        return self._with_suggestions({
            'answer': (
                "Pour reserver un livre, ouvrez le detail du livre depuis le catalogue, puis cliquez sur le bouton Reserver. "
                "Si le livre est disponible ou si une file d'attente existe, votre reservation est enregistree et vous pouvez suivre son etat dans Mes reservations."
            ),
            'results': [],
            'actions': [{'label': 'Voir mes reservations', 'url': reverse('reservations:list')}, {'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
        }, 'reservation')

    def _account_answer(self):
        actions = []
        if self._is_authenticated():
            actions.extend([
                {'label': 'Mon compte', 'url': reverse('accounts:account')},
                {'label': 'Modifier profil', 'url': reverse('accounts:profile_edit')},
                {'label': 'Mes reclamations', 'url': reverse('accounts:complaints')},
                {'label': 'Wishlist', 'url': reverse('catalog:wishlist')},
            ])
            answer = (
                "Depuis ton espace compte, tu peux consulter ton profil, tes commandes, tes emprunts, tes reservations, "
                "ta wishlist et tes reclamations. Pour une reclamation, choisis une categorie, une priorite, puis envoie ton message a l'administration."
            )
        else:
            actions.extend([
                {'label': 'Connexion', 'url': reverse('accounts:login')},
                {'label': 'Inscription', 'url': reverse('accounts:register')},
            ])
            answer = (
                "Tu peux creer un compte ou te connecter pour acceder au profil, aux emprunts, reservations, commandes, wishlist et reclamations. "
                "Les pages personnelles demandent une authentification."
            )
        return self._with_suggestions({'answer': answer, 'results': [], 'actions': actions}, 'account')

    def _login_answer(self):
        return self._with_suggestions({
            'answer': INTENT_KNOWLEDGE['login']['answer'],
            'results': [],
            'actions': [{'label': 'Connexion', 'url': reverse('accounts:login')}],
        }, 'login')

    def _register_answer(self):
        return self._with_suggestions({
            'answer': INTENT_KNOWLEDGE['register']['answer'],
            'results': [],
            'actions': [{'label': 'Inscription', 'url': reverse('accounts:register')}],
        }, 'register')

    def _profile_answer(self):
        actions = [{'label': 'Connexion', 'url': reverse('accounts:login')}]
        if self._is_authenticated():
            actions = [
                {'label': 'Mon compte', 'url': reverse('accounts:account')},
                {'label': 'Modifier profil', 'url': reverse('accounts:profile_edit')},
            ]
        return self._with_suggestions({
            'answer': INTENT_KNOWLEDGE['profile']['answer'],
            'results': [],
            'actions': actions,
        }, 'profile')

    def _complaint_answer(self):
        return self._with_suggestions({
            'answer': (
                "Pour envoyer une reclamation, ouvrez la page Reclamations, choisissez la categorie du probleme, "
                "definissez la priorite puis decrivez clairement la situation. L'administration pourra suivre et repondre a votre message."
            ),
            'results': [],
            'actions': [{'label': 'Mes reclamations', 'url': reverse('accounts:complaints')}],
        }, 'complaint')

    def _contact_answer(self):
        actions = [{'label': 'Reclamation', 'url': reverse('accounts:complaints')}]
        if not self._is_authenticated():
            actions.insert(0, {'label': 'Connexion', 'url': reverse('accounts:login')})
        return self._with_suggestions({
            'answer': (
                "Pour contacter le support BiblioNUM, utilisez une reclamation depuis votre compte. "
                "C'est le meilleur endroit pour signaler un probleme de commande, paiement, emprunt, reservation ou profil."
            ),
            'results': [],
            'actions': actions,
        }, 'contact')

    def _admin_answer(self):
        return self._with_suggestions({
            'answer': (
                "L'administrateur gere le backoffice BiblioNUM: livres, auteurs, categories, stock, utilisateurs, commandes, "
                "paiements, factures, emprunts, reservations et reclamations. Le tableau de bord sert aussi a suivre les indicateurs importants."
            ),
            'results': [],
            'actions': [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
        }, 'admin')

    def _stock_answer(self):
        return self._with_suggestions({
            'answer': (
                "Le stock indique les exemplaires disponibles pour chaque livre. Si aucun exemplaire n'est disponible, le livre peut etre marque indisponible "
                "ou etre reserve selon le cas. Une commande payee ou un emprunt valide diminue le stock; un retour d'emprunt l'augmente."
            ),
            'results': [],
            'actions': [{'label': 'Voir le catalogue', 'url': reverse('catalog:books_list')}],
        }, 'stock')

    def _history_answer(self):
        actions = self._common_actions()
        if self._is_authenticated():
            actions = [
                {'label': 'Mes commandes', 'url': reverse('orders:orders_list')},
                {'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')},
                {'label': 'Mes reservations', 'url': reverse('reservations:list')},
                {'label': 'Mes reclamations', 'url': reverse('accounts:complaints')},
            ]
        return self._with_suggestions({
            'answer': INTENT_KNOWLEDGE['history']['answer'],
            'results': [],
            'actions': actions,
        }, 'history')

    def _categories_answer(self):
        categories = Category.objects.order_by('name')
        names = ', '.join(categories.values_list('name', flat=True)[:22])
        return self._with_suggestions({
            'answer': f"Le catalogue contient {categories.count()} domaines. Les principaux sont: {names}. Tu peux me dire: montre les livres Finance ou livres Medecine moins de 150 DH.",
            'results': [],
            'actions': [{'label': 'Explorer le catalogue', 'url': reverse('catalog:books_list')}],
        }, 'category')

    def _authors_answer(self):
        author = self._find_author()
        authors = Author.objects.order_by('last_name', 'first_name')
        if author:
            authors = Author.objects.filter(id=author.id)
        visible = authors[: self.MAX_RESULTS]
        return self._with_suggestions({
            'answer': f"J'ai trouve {authors.count()} auteur(s).",
            'results': [self._author_result(author) for author in visible],
            'actions': [{'label': 'Tous les livres', 'url': reverse('catalog:books_list')}],
        }, 'author')

    def _catalog_search(self):
        filters = self._extract_filters()
        previous_filters = self.context.get('filters') or {}
        if self._is_follow_up() and previous_filters:
            filters = {**previous_filters, **{key: value for key, value in filters.items() if value not in (None, '', False)}}

        if self._needs_catalog_clarification(filters):
            return self._with_suggestions({
                'answer': (
                    "Bien sur. Tu cherches un livre dans quel domaine ? "
                    "Par exemple: marketing, finance, informatique, data science, roman ou developpement personnel."
                ),
                'results': [],
                'actions': [{'label': 'Voir le catalogue', 'url': reverse('catalog:books_list')}],
            }, 'catalog')

        books = self._apply_book_filters(Book.objects.filter(status='available').select_related('author', 'category'), filters)
        count = books.count()

        self._save_context('catalog', filters)
        if count == 0:
            fallback = self._relaxed_search(filters) if self._has_structured_filter(filters) else Book.objects.none()
            if fallback.exists():
                return self._with_suggestions({
                    'answer': "Je n'ai pas trouve exactement avec tous les criteres, mais voici des resultats proches.",
                    'results': [self._book_result(book) for book in fallback[: self.MAX_RESULTS]],
                    'actions': [{'label': 'Ouvrir le catalogue', 'url': reverse('catalog:books_list')}],
                }, 'catalog')
            return self._unknown_answer()

        intro = self._catalog_intro(count, filters)
        return self._with_suggestions({
            'answer': intro,
            'results': [self._book_result(book) for book in books[: self.MAX_RESULTS]],
            'actions': [{'label': 'Voir tous les resultats', 'url': self._catalog_url(filters)}],
        }, 'catalog')

    def _extract_filters(self):
        category = self._find_category()
        author = self._find_author()
        min_price, max_price = self._extract_price_range()
        cleaned = self._clean_search_terms(self.message, category=category, author=author)
        return {
            'category_id': category.id if category else None,
            'author_id': author.id if author else None,
            'min_price': str(min_price) if min_price is not None else None,
            'max_price': str(max_price) if max_price is not None else None,
            'available_only': self._matches('disponible', 'disponibles', 'dispo', 'stock'),
            'sort': self._extract_sort(),
            'query': cleaned,
        }

    def _apply_book_filters(self, books, filters):
        if filters.get('category_id'):
            books = books.filter(category_id=filters['category_id'])
        if filters.get('author_id'):
            books = books.filter(author_id=filters['author_id'])
        if filters.get('min_price'):
            books = books.filter(price__gte=Decimal(filters['min_price']))
        if filters.get('max_price'):
            books = books.filter(price__lte=Decimal(filters['max_price']))
        if filters.get('available_only'):
            books = books.filter(available_copies__gt=0)
        if filters.get('query'):
            query = filters['query']
            books = books.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(isbn__icontains=query)
                | Q(author__first_name__icontains=query)
                | Q(author__last_name__icontains=query)
                | Q(category__name__icontains=query)
            ).distinct()

        if filters.get('sort') == 'cheap':
            return books.order_by('price', '-rating')
        if filters.get('sort') == 'rating':
            return books.order_by('-rating', '-number_of_reviews', '-available_copies')
        if filters.get('sort') == 'newest':
            return books.order_by('-created_at', '-rating')
        return books.order_by('-rating', 'price')

    def _relaxed_search(self, filters):
        relaxed = dict(filters)
        relaxed['query'] = ''
        return self._apply_book_filters(Book.objects.filter(status='available').select_related('author', 'category'), relaxed)

    def _catalog_intro(self, count, filters):
        details = []
        if filters.get('category_id'):
            category = Category.objects.filter(id=filters['category_id']).first()
            if category:
                details.append(f"domaine {category.name}")
        if filters.get('author_id'):
            author = Author.objects.filter(id=filters['author_id']).first()
            if author:
                details.append(f"auteur {author}")
        if filters.get('max_price'):
            details.append(f"prix <= {filters['max_price']} DH")
        if filters.get('min_price'):
            details.append(f"prix >= {filters['min_price']} DH")
        if filters.get('available_only'):
            details.append("disponibles en stock")
        if filters.get('sort') == 'cheap' and not filters.get('max_price'):
            details.append("les moins chers")
        if filters.get('sort') == 'rating':
            details.append("les mieux notes")
        if filters.get('sort') == 'newest':
            details.append("nouveautes")

        suffix = f" ({', '.join(details)})" if details else ''
        return f"J'ai compris ta recherche{suffix}. J'ai trouve {count} livre(s); voici les meilleurs resultats."

    def _book_result(self, book):
        availability = 'disponible' if book.is_available() else 'indisponible'
        borrow_fee = (book.price * Decimal('0.30')).quantize(Decimal('0.01'))
        return {
            'title': book.title,
            'meta': f"{book.author} - {book.category.name if book.category else 'Sans categorie'}",
            'detail': f"{book.price} DH, emprunt {borrow_fee} DH, stock {book.available_copies}/{book.total_copies}, {availability}, note {book.rating}/5.",
            'url': reverse('catalog:book_detail', args=[book.slug]),
            'cover': book.get_cover_image_url(),
        }

    def _borrow_result(self, borrow):
        return {
            'title': borrow.book.title,
            'meta': f"{borrow.get_status_display()} - paiement {borrow.get_payment_status_display()}",
            'detail': f"A rendre avant le {borrow.due_date:%d/%m/%Y}. Montant: {borrow.amount_due} DH.",
            'url': reverse('borrowing:borrow_detail', args=[borrow.id]),
            'cover': borrow.book.get_cover_image_url(),
        }

    def _borrow_request_result(self, request):
        return {
            'title': request.book.title,
            'meta': f"Demande {request.get_status_display()}",
            'detail': f"Demandee le {request.requested_date:%d/%m/%Y}.",
            'url': reverse('catalog:book_detail', args=[request.book.slug]),
            'cover': request.book.get_cover_image_url(),
        }

    def _order_result(self, order):
        return {
            'title': order.order_number,
            'meta': f"{order.payment_state_label} - {order.get_status_display()}",
            'detail': f"Total {order.total} DH. {order.payment_state_hint}",
            'url': reverse('orders:order_detail', args=[order.id]),
            'cover': '',
        }

    def _reservation_result(self, reservation):
        return {
            'title': reservation.book.title,
            'meta': reservation.get_status_display(),
            'detail': f"Position {reservation.queue_position}. Expire le {reservation.expiration_date:%d/%m/%Y}.",
            'url': reverse('reservations:detail', args=[reservation.id]),
            'cover': reservation.book.get_cover_image_url(),
        }

    def _author_result(self, author):
        return {
            'title': str(author).strip(),
            'meta': author.nationality or 'Auteur',
            'detail': f"{author.books.count()} livre(s) dans le catalogue.",
            'url': reverse('catalog:author_books', args=[author.id]),
            'cover': '',
        }

    def _catalog_url(self, filters):
        params = {}
        if filters.get('query'):
            params['q'] = filters['query']
        if filters.get('category_id'):
            params['category'] = filters['category_id']
        if filters.get('author_id'):
            params['author'] = filters['author_id']
        if filters.get('min_price'):
            params['min_price'] = filters['min_price']
        if filters.get('max_price'):
            params['max_price'] = filters['max_price']
        if filters.get('sort') == 'cheap':
            params['sort'] = 'price_low'
        elif filters.get('sort') == 'rating':
            params['sort'] = 'rating'
        url = reverse('catalog:books_list')
        return f'{url}?{urlencode(params)}' if params else url

    def _find_category(self):
        aliases = {
            'ia': 'intelligence artificielle',
            'ai': 'intelligence artificielle',
            'cyber': 'cybersecurite',
            'securite': 'cybersecurite',
            'ux': 'design ux',
            'design': 'design ux',
            'medecin': 'medecine',
            'medical': 'medecine',
            'eco': 'economie',
            'business': 'business',
            'developpement': 'developpement personnel',
            'personnel': 'developpement personnel',
            'dev personnel': 'developpement personnel',
            'roman': 'romance',
            'marketing': 'marketing',
            'finance': 'finance',
            'informatique': 'informatique',
            'data': 'data science',
            'science donnees': 'data science',
        }
        for source, target in aliases.items():
            if source in self.tokens or (' ' in source and source in self.normalized):
                match = Category.objects.filter(name__iexact=target).first()
                if match:
                    return match

        for category in Category.objects.all():
            name = self._normalize(category.name)
            if name in self.normalized or any(len(token) > 2 and (token == name or name.startswith(token)) for token in self.tokens):
                return category
        return None

    def _find_author(self):
        for author in Author.objects.all():
            full_name = self._normalize(str(author).strip())
            if full_name and full_name in self.normalized:
                return author
            parts = [self._normalize(author.first_name), self._normalize(author.last_name)]
            if author.last_name and any(part in self.tokens for part in parts if len(part) > 2):
                return author
        return None

    def _extract_price_range(self):
        min_price = None
        max_price = None
        amount_match = re.search(
            r'(?:(moins\s+de|inferieur\s+a|prix\s*<=|<|max(?:imum)?|prix|plus\s+de|min(?:imum)?)\s*)?(\d+(?:[.,]\d+)?)\s*(dh|mad)?',
            self.normalized,
        )
        if not amount_match:
            return min_price, max_price
        if not amount_match.group(1) and not amount_match.group(3):
            return min_price, max_price

        try:
            amount = Decimal(amount_match.group(2).replace(',', '.'))
        except InvalidOperation:
            return min_price, max_price

        if self._matches('moins', 'max', 'maximum', 'inferieur', 'pas cher', 'moins cher', 'ne depasse pas'):
            max_price = amount
        elif self._matches('plus', 'min', 'minimum', 'superieur'):
            min_price = amount
        else:
            max_price = amount
        return min_price, max_price

    def _clean_search_terms(self, text, category=None, author=None):
        normalized = self._normalize(text)
        if category:
            normalized = normalized.replace(self._normalize(category.name), ' ')
        if author:
            normalized = normalized.replace(self._normalize(str(author)), ' ')

        stop_words = {
            'je', 'veux', 'svp', 'stp', 'possible', 'donne', 'affiche', 'montre',
            'livre', 'livres', 'chercher', 'cherche', 'recherche', 'trouve', 'moi',
            'avec', 'dans', 'categorie', 'domain', 'domaine', 'domaines', 'theme',
            'moins', 'plus', 'max', 'min', 'maximum', 'minimum', 'inferieur', 'superieur',
            'disponible', 'disponibles', 'dispo', 'stock', 'top', 'meilleur', 'meilleurs',
            'note', 'prix', 'dh', 'mad', 'de', 'des', 'du', 'un', 'une', 'les', 'le', 'la',
            'pas', 'cher', 'chere', 'recommande', 'recommendation',
            'bonjour', 'salut', 'hello', 'merci', 'aide', 'nouveau', 'nouveaux',
            'nouveaute', 'nouveautes', 'voir', 'peux', 'peut',
        }
        words = [word for word in re.findall(r'[a-z0-9]+', normalized) if word not in stop_words and not word.isdigit()]
        return ' '.join(words[:6]).strip()

    def _extract_sort(self):
        if self._matches('nouveaute', 'nouveautes', 'recent', 'recents', 'nouveau', 'nouveaux'):
            return 'newest'
        if self._matches('meilleur', 'top', 'note', 'populaire', 'recommande'):
            return 'rating'
        if self._matches('pas cher', 'moins cher', 'economique'):
            return 'cheap'
        return ''

    def _detect_intent(self):
        scores = {intent: 0 for intent in self.INTENTS}
        for intent, data in INTENT_KNOWLEDGE.items():
            for phrase in data.get('phrases', ()):
                normalized = self._normalize(phrase)
                if normalized and normalized in self.normalized:
                    scores[intent] += 5
            for keyword in data.get('keywords', ()):
                normalized = self._normalize(keyword)
                if not normalized:
                    continue
                if ' ' in normalized:
                    if normalized in self.normalized:
                        scores[intent] += 4
                    continue
                if normalized in self.tokens:
                    scores[intent] += 3 if len(normalized) > 4 else 2
                elif len(normalized) > 4 and any(self._similar_token(token, normalized) for token in self.tokens):
                    scores[intent] += 1

        if self._find_category() or self._find_author() or self._extract_price_range() != (None, None):
            scores['book_search'] += 4
        if self._matches('livre', 'livres', 'ouvrage', 'bouquin') and self._matches('chercher', 'trouver', 'recherche', 'titre', 'auteur'):
            scores['book_search'] += 4
        if self._matches('prendre un livre'):
            scores['borrow'] += 4
            scores['reservation'] += 2
        if self._is_follow_up() and self.context.get('intent'):
            scores[self.context['intent']] = scores.get(self.context['intent'], 0) + 2

        best_intent, best_score = max(scores.items(), key=lambda item: item[1])
        if best_score < 2:
            return 'unknown'
        return best_intent

    def _is_follow_up(self):
        return bool(
            self.context
            and (
                self._matches('moins', 'plus cher', 'seulement', 'aussi', 'encore', 'autre', 'max', 'minimum', 'maximum', 'inferieur', 'disponible', 'disponibles', 'dispo', 'stock')
                and not self._matches('livre', 'livres')
            )
        )

    def _is_too_short(self):
        return len(self.normalized) <= 1 or (len(self.tokens) == 1 and len(self.tokens[0]) <= 1)

    def _clarify(self):
        last_intent = self.context.get('intent')
        if last_intent == 'catalog':
            return self._with_suggestions({
                'answer': "Je n'ai pas assez d'information. Tu peux continuer avec un domaine, un auteur ou un prix: par exemple moins de 200 DH ou seulement disponibles.",
                'results': [],
                'actions': [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}],
            }, 'catalog')
        return self._with_suggestions({
            'answer': CLARIFICATIONS['short']['answer'],
            'results': [],
            'actions': self._common_actions(),
            'suggestions': CLARIFICATIONS['short']['suggestions'],
        }, 'help')

    def _needs_catalog_clarification(self, filters):
        return (
            self._matches('livre', 'livres', 'chercher', 'cherche', 'recherche')
            and not self._has_structured_filter(filters)
            and not filters.get('query')
        )

    def _has_structured_filter(self, filters):
        return any([
            filters.get('category_id'),
            filters.get('author_id'),
            filters.get('min_price'),
            filters.get('max_price'),
            filters.get('available_only'),
            filters.get('sort'),
        ])

    def _unknown_answer(self):
        return self._with_suggestions({
            'answer': (
                "Je peux vous aider avec la recherche d'un livre, une reservation, un emprunt, une commande, "
                "un paiement, une facture ou une reclamation. Choisissez un raccourci ci-dessous ou reformulez en quelques mots."
            ),
            'results': [],
            'actions': self._common_actions(),
        }, 'help')

    def _is_gibberish(self):
        if len(self.tokens) == 1 and len(self.tokens[0]) >= 7:
            token = self.tokens[0]
            has_vowel = any(char in token for char in 'aeiouy')
            known = any(keyword in token for words in self.INTENTS.values() for keyword in [self._normalize(word).replace(' ', '') for word in words])
            return not has_vowel and not known
        return False

    def _is_personal_question(self):
        return self._matches('mes', 'mon', 'ma', 'suivi', 'statut', 'etat', 'historique', 'a moi', 'mes derniers')

    def _is_authenticated(self):
        return bool(getattr(self.user, 'is_authenticated', False))

    def _login_required_answer(self, message):
        return self._with_suggestions({
            'answer': message,
            'results': [],
            'actions': [{'label': 'Connexion', 'url': reverse('accounts:login')}],
        }, 'account')

    def _common_actions(self):
        actions = [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}]
        if self._is_authenticated():
            actions.extend(
                [
                    {'label': 'Mes commandes', 'url': reverse('orders:orders_list')},
                    {'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')},
                    {'label': 'Mes reservations', 'url': reverse('reservations:list')},
                ]
            )
        else:
            actions.append({'label': 'Connexion', 'url': reverse('accounts:login')})
        return actions

    def _actions_for_intent(self, intent):
        if intent in ('catalog', 'book_search', 'book_detail'):
            return [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}]
        if intent == 'stock':
            return [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}]
        if intent == 'payment':
            return [{'label': 'Panier', 'url': reverse('cart:cart')}, {'label': 'Mes commandes', 'url': reverse('orders:orders_list')}]
        if intent == 'order':
            return [{'label': 'Panier', 'url': reverse('cart:cart')}, {'label': 'Mes commandes', 'url': reverse('orders:orders_list')}]
        if intent == 'invoice':
            return [{'label': 'Mes commandes', 'url': reverse('orders:orders_list')}]
        if intent == 'borrow':
            return [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}, {'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')}]
        if intent == 'return':
            return [{'label': 'Mes emprunts', 'url': reverse('borrowing:borrow_list')}]
        if intent == 'reservation':
            return [{'label': 'Catalogue', 'url': reverse('catalog:books_list')}, {'label': 'Mes reservations', 'url': reverse('reservations:list')}]
        if intent in ('complaint', 'contact'):
            return [{'label': 'Mes reclamations', 'url': reverse('accounts:complaints')}]
        if intent == 'account':
            if self._is_authenticated():
                return [{'label': 'Mon compte', 'url': reverse('accounts:account')}, {'label': 'Mes reclamations', 'url': reverse('accounts:complaints')}]
            return [{'label': 'Connexion', 'url': reverse('accounts:login')}, {'label': 'Inscription', 'url': reverse('accounts:register')}]
        if intent == 'login':
            return [{'label': 'Connexion', 'url': reverse('accounts:login')}]
        if intent == 'register':
            return [{'label': 'Inscription', 'url': reverse('accounts:register')}]
        if intent == 'profile':
            if self._is_authenticated():
                return [{'label': 'Modifier profil', 'url': reverse('accounts:profile_edit')}]
            return [{'label': 'Connexion', 'url': reverse('accounts:login')}]
        if intent == 'history':
            return self._common_actions()
        return self._common_actions()

    def _remember(self, intent, response):
        self._save_context(intent, self.context.get('filters', {}))
        return response

    def _with_suggestions(self, response, intent):
        response.setdefault('results', [])
        response.setdefault('actions', [])
        response.setdefault('suggestions', self._suggestions_for(intent))
        return response

    def _suggestions_for(self, intent):
        if intent in INTENT_KNOWLEDGE:
            return list(INTENT_KNOWLEDGE[intent].get('suggestions', DEFAULT_SUGGESTIONS))
        suggestions = {
            'catalog': ['Catalogue', 'Chercher un livre disponible', 'Top livres Data Science', 'Livres par auteur'],
            'book_search': ['Chercher un livre', 'Livres disponibles', 'Livres pas chers', 'Catalogue'],
            'book_detail': ['Detail d un livre', 'Chercher un livre', 'Reserver un livre'],
            'stock': ['Livre indisponible', 'Livres disponibles', 'Comment reserver un livre ?'],
            'borrow': ['Comment emprunter un livre ?', 'Mes emprunts actifs', 'Que se passe-t-il en retard ?'],
            'return': ['Comment rendre un livre ?', 'Mes emprunts', 'Retard et amende'],
            'payment': ['Comment payer une commande ?', 'Mes commandes en attente', 'Ouvrir mon panier'],
            'order': ['Mes commandes', 'Statut de commande', 'Ouvrir mon panier'],
            'invoice': ['Facture commande', 'Mes commandes', 'Paiement'],
            'cart': ['Panier', 'Comment ajouter au panier ?', 'Chercher un livre disponible'],
            'reservation': ['Comment reserver un livre ?', 'Mes reservations actives', 'Annuler une reservation'],
            'account': ['Compte utilisateur', 'Comment modifier mon profil ?', 'Voir ma wishlist'],
            'login': ['Connexion', 'Mot de passe oublie', 'Inscription'],
            'register': ['Inscription', 'Connexion', 'Compte utilisateur'],
            'profile': ['Modifier profil', 'Mot de passe oublie', 'Compte utilisateur'],
            'complaint': ['Envoyer une reclamation', 'Probleme paiement', 'Probleme emprunt'],
            'contact': ['Contacter le support', 'Envoyer une reclamation', 'Probleme commande'],
            'admin': ['Role administrateur', 'Gestion du stock', 'Commandes et paiements'],
            'history': ['Mes commandes', 'Mes emprunts', 'Mes reservations', 'Reclamation'],
            'greeting': ['Catalogue', 'Chercher un livre', 'Reserver un livre', 'Paiement'],
            'category': ['Quelles categories existent ?', 'Livres Intelligence artificielle', 'Livres Business'],
            'author': ['Trouver un auteur', 'Livres de Martin Kleppmann', 'Tous les livres'],
            'help': ['Catalogue', 'Chercher un livre', 'Mes commandes', 'Paiement', 'Panier', 'Reclamation'],
        }
        return suggestions.get(intent, suggestions['help'])

    def _save_context(self, intent, filters=None):
        self.context = {'intent': intent, 'filters': filters or {}, 'last_message': self.message}
        if self.session is not None:
            self.session[self.CONTEXT_KEY] = self.context
            self.session.modified = True

    def _matches(self, *words):
        return any(self._normalize(word) in self.normalized for word in words)

    @staticmethod
    def _similar_token(token, keyword):
        if abs(len(token) - len(keyword)) > 2 or len(token) < 4:
            return False
        if token[0] != keyword[0]:
            return False
        if token == keyword:
            return True
        prefix = min(4, len(keyword), len(token))
        if prefix >= 3 and token[:prefix] == keyword[:prefix]:
            return True
        return False

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize('NFKD', value or '')
        value = ''.join(char for char in value if not unicodedata.combining(char))
        value = value.lower()
        value = re.sub(r"[-_']", ' ', value)
        replacements = {
            'paiment': 'paiement',
            'piement': 'paiement',
            'payement': 'paiement',
            'commend': 'commande',
            'comande': 'commande',
            'commende': 'commande',
            'emprun ': 'emprunt ',
            'emprunterr': 'emprunter',
            'resrvation': 'reservation',
            'reservasion': 'reservation',
            'catigorie': 'categorie',
            'categori': 'categorie',
            'liver': 'livre',
            'livree': 'livre',
            'livr ': 'livre ',
            'biblio': 'bibliotheque',
            'biblotheque': 'bibliotheque',
            'biblioteque': 'bibliotheque',
            'deppase': 'depasse',
            'depasse': 'depasse',
            'inteligeant': 'intelligent',
            'fonctionalite': 'fonctionnalite',
            'fonctuenelle': 'fonctionnelle',
            'metier': 'metier',
            'lametier': 'metier',
            'reserverr': 'reserver',
        }
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
