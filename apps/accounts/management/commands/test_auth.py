"""
Test de diagnostic pour l'authentification
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from apps.accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Test d\'authentification'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Diagnostic d\'authentification\n')
        
        # Vérifier les utilisateurs
        self.stdout.write('📊 Utilisateurs dans la base:')
        users = CustomUser.objects.all()
        for user in users:
            self.stdout.write(f'  - {user.username} | Email: {user.email} | Active: {user.is_active}')
        
        # Tester l'authentification
        self.stdout.write('\n🔐 Test d\'authentification:')
        test_cases = [
            ('john', 'password123'),
            ('jane', 'password123'),
            ('admin', 'admin123'),
            ('john', 'wrongpassword'),
        ]
        
        for username, password in test_cases:
            user = authenticate(username=username, password=password)
            status = '✅ SUCCESS' if user else '❌ FAILED'
            self.stdout.write(f'  {status} - {username}:{password}')
            if user:
                self.stdout.write(f'    ↳ User: {user.get_full_name()} | Active: {user.is_active}')
        
        # Vérifier les propriétés d'authentification
        self.stdout.write('\n⚙️ Configuration Django:')
        from django.conf import settings
        self.stdout.write(f'  - SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}')
        self.stdout.write(f'  - SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}')
        self.stdout.write(f'  - CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}')
        self.stdout.write(f'  - CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}')
        self.stdout.write(f'  - DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'  - AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}')
