import json
import logging

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import ChatConversation, ChatMessage
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
        answer = assistant.answer(question)
        save_chat_exchange(request, question, answer)
        return JsonResponse(answer, json_dumps_params={'ensure_ascii': False})
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


def save_chat_exchange(request, question, answer):
    if not request.session.session_key:
        request.session.create()

    conversation_id = request.session.get('chatbot_conversation_id')
    conversation = None
    if conversation_id:
        conversation = ChatConversation.objects.filter(pk=conversation_id).first()

    if not conversation:
        title = question[:80] or 'Conversation chatbot'
        conversation = ChatConversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or '',
            title=title,
        )
        request.session['chatbot_conversation_id'] = conversation.pk
    elif request.user.is_authenticated and conversation.user_id is None:
        conversation.user = request.user
        conversation.save(update_fields=['user', 'updated_at'])

    ChatMessage.objects.create(conversation=conversation, role='user', content=question)
    ChatMessage.objects.create(
        conversation=conversation,
        role='assistant',
        content=answer.get('answer', ''),
        metadata={
            'intent': answer.get('intent'),
            'source': answer.get('source'),
            'actions': answer.get('actions', []),
        },
    )


@login_required
def conversation_list(request):
    conversations = request.user.chat_conversations.prefetch_related('messages')[:30]
    return render(request, 'chatbot/conversations.html', {'conversations': conversations})


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        request.user.chat_conversations.prefetch_related('messages'),
        pk=pk,
    )
    return render(request, 'chatbot/conversation_detail.html', {'conversation': conversation})
