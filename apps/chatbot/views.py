import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import LibraryAssistant

logger = logging.getLogger(__name__)


@require_POST
def ask_chatbot(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    question = (payload.get('message') or '').strip()
    if not question:
        return JsonResponse(
            {
                'answer': 'Écrivez une question ou une recherche, par exemple : livres de Data Science disponibles.',
                'results': [],
                'actions': [],
                'suggestions': [
                    'Catalogue',
                    'Chercher un livre',
                    'Mes commandes',
                    'Paiement',
                ],
            },
            status=400,
            json_dumps_params={'ensure_ascii': False},
        )

    if len(question) > 500:
        return JsonResponse(
            {
                'answer': 'Votre question est trop longue. Résumez-la en une ou deux phrases pour que je puisse vous aider efficacement.',
                'results': [],
                'actions': [],
                'suggestions': ['Chercher un livre', 'Paiement', 'Mes réservations', 'Réclamation'],
            },
            status=400,
            json_dumps_params={'ensure_ascii': False},
        )

    try:
        assistant = LibraryAssistant(request.user, request.session)
        return JsonResponse(assistant.answer(question), json_dumps_params={'ensure_ascii': False})
    except Exception:
        logger.exception('Erreur chatbot pour user=%s', getattr(request.user, 'id', None))
        return JsonResponse(
            {
                'answer': (
                    "Je n'arrive pas à traiter cette demande pour le moment. "
                    "Réessayez avec une question plus simple ou utilisez les raccourcis ci-dessous."
                ),
                'results': [],
                'actions': [],
                'suggestions': ['Catalogue', 'Comment emprunter ?', 'Paiement', 'Panier'],
            },
            status=500,
            json_dumps_params={'ensure_ascii': False},
        )
