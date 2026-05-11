from django.conf import settings
from django.core.management.base import BaseCommand

from apps.chatbot.ai import generate_ai_response


class Command(BaseCommand):
    help = "Teste l'appel IA du chatbot BiblioNUM sans exposer la cle API."

    def add_arguments(self, parser):
        parser.add_argument(
            'message',
            nargs='?',
            default='Explique comment reserver un livre dans BiblioNUM.',
            help='Message de test envoye a l IA.',
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        configured = bool(api_key and api_key != 'sk-xxx')

        self.stdout.write(f"CHATBOT_MODE={getattr(settings, 'CHATBOT_MODE', 'local')}")
        self.stdout.write(f"CHATBOT_MODEL={getattr(settings, 'CHATBOT_MODEL', '')}")
        self.stdout.write(f"OPENAI_API_KEY configured={configured}")

        if not configured:
            self.stdout.write(self.style.WARNING("Cle API absente ou placeholder. Aucun appel IA reel ne sera effectue."))
            return

        answer = generate_ai_response(options['message'], {'intent': 'debug', 'last_message': ''})
        if answer:
            self.stdout.write(self.style.SUCCESS("IA appelee avec succes."))
            self.stdout.write(answer)
        else:
            self.stdout.write(self.style.ERROR("L'appel IA a echoue ou n'a retourne aucune reponse."))
