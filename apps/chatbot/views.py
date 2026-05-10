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
                'answer': 'Ecris une question ou une recherche, par exemple: livres de Data Science disponibles.',
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
        )

    if len(question) > 500:
        return JsonResponse(
            {
                'answer': 'Ta question est trop longue. Resume-la en une ou deux phrases pour que je puisse t aider efficacement.',
                'results': [],
                'actions': [],
                'suggestions': ['Chercher un livre', 'Paiement', 'Mes reservations', 'Reclamation'],
            },
            status=400,
        )

    try:
        assistant = LibraryAssistant(request.user, request.session)
        return JsonResponse(assistant.answer(question))
    except Exception:
        logger.exception('Erreur chatbot pour user=%s', getattr(request.user, 'id', None))
        return JsonResponse(
            {
                'answer': (
                    "Je n'arrive pas a traiter cette demande pour le moment. "
                    "Reessaie avec une question plus simple ou utilise les raccourcis ci-dessous."
                ),
                'results': [],
                'actions': [],
                'suggestions': ['Catalogue', 'Comment emprunter ?', 'Paiement', 'Panier'],
            },
            status=500,
        )
