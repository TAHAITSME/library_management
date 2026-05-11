import logging
import json
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


BIBLIONUM_SYSTEM_CONTEXT = """
Tu es l'assistant IA de BiblioNUM, une application web de gestion de bibliotheque.

BiblioNUM permet aux utilisateurs de:
- consulter le catalogue;
- rechercher un livre;
- voir le detail d'un livre;
- reserver un livre;
- emprunter un livre;
- retourner un livre;
- gerer le panier;
- passer une commande;
- effectuer un paiement;
- generer ou consulter une facture;
- suivre les commandes;
- suivre les emprunts;
- suivre les reservations;
- envoyer une reclamation;
- gerer le profil utilisateur.

L'administrateur peut:
- gerer les livres;
- gerer le stock;
- gerer les utilisateurs;
- gerer les commandes;
- gerer les emprunts;
- gerer les reservations;
- traiter les reclamations;
- consulter le tableau de bord.

Regles de reponse:
- Reponds en francais, de facon claire, professionnelle et utile.
- Reste dans le contexte de BiblioNUM.
- Ne promets pas une fonctionnalite non decrite ci-dessus.
- Si tu n'es pas certain qu'une fonctionnalite existe, dis exactement:
  "Je ne suis pas certain que cette fonctionnalite soit disponible dans l'application actuelle."
- Donne des etapes simples quand c'est pertinent.
- Reponse courte: 2 a 5 phrases maximum.
""".strip()


def _has_usable_api_key():
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    return bool(api_key and api_key != 'sk-xxx' and api_key.startswith('sk-'))


def _compact_context(context):
    if not context:
        return 'Aucun contexte precedent.'
    intent = context.get('intent') or 'inconnu'
    last_message = context.get('last_message') or ''
    return f"Derniere intention locale: {intent}. Dernier message: {last_message[:180]}"


def generate_ai_response(message, context=None):
    """Genere une reponse IA courte pour les cas non couverts localement.

    Retourne None si la configuration est absente ou si l'API est indisponible.
    """
    cleaned = str(message or '').strip()
    if not cleaned or len(cleaned) > getattr(settings, 'CHATBOT_AI_MAX_INPUT', 500):
        return None
    if not _has_usable_api_key():
        return None

    payload = _build_payload(cleaned, context)
    return _generate_with_sdk(payload) or _generate_with_http(payload)


def _build_payload(message, context):
    return {
        'model': getattr(settings, 'CHATBOT_MODEL', 'gpt-4.1-mini'),
        'instructions': BIBLIONUM_SYSTEM_CONTEXT,
        'input': [
            {
                'role': 'user',
                'content': (
                    f"Contexte conversationnel: {_compact_context(context)}\n"
                    f"Message utilisateur: {message}"
                ),
            }
        ],
        'max_output_tokens': getattr(settings, 'CHATBOT_AI_MAX_OUTPUT', 220),
    }


def _generate_with_sdk(payload):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(**payload)
    except Exception:
        logger.info('SDK OpenAI indisponible, tentative via HTTP direct', exc_info=True)
        return None

    return _extract_response_text(response)


def _generate_with_http(payload):
    body = json.dumps(payload).encode('utf-8')
    req = request.Request(
        'https://api.openai.com/v1/responses',
        data=body,
        headers={
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=18) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (error.HTTPError, error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        logger.exception('Erreur HTTP OpenAI chatbot')
        return None
    return _extract_response_text(data)


def _extract_response_text(response):
    text = getattr(response, 'output_text', '') or ''
    if text:
        return text.strip()

    if isinstance(response, dict):
        output = response.get('output') or []
        chunks = []
        for item in output:
            for content in item.get('content') or []:
                if content.get('type') in ('output_text', 'text'):
                    chunks.append(content.get('text') or '')
        return ' '.join(chunk.strip() for chunk in chunks if chunk).strip() or None

    try:
        for item in getattr(response, 'output', []) or []:
            for content in getattr(item, 'content', []) or []:
                text += getattr(content, 'text', '') or ''
    except Exception:
        text = ''
    return text.strip() or None
