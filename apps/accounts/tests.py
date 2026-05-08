from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse


class ProfileAvatarTests(TestCase):
    def test_profile_edit_saves_uploaded_avatar(self):
        user = get_user_model().objects.create_user(
            username='avatar-user',
            email='avatar@example.com',
            password='secret',
            first_name='Avatar',
            last_name='User',
        )
        client = Client()
        client.force_login(user)

        image = SimpleUploadedFile(
            'avatar.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif',
        )

        with patch(
            'django.core.files.storage.filesystem.FileSystemStorage._save',
            return_value='accounts/avatars/avatar.gif',
        ):
            response = client.post(reverse('accounts:profile_edit'), {
                'first_name': 'Avatar',
                'last_name': 'User',
                'email': 'avatar@example.com',
                'phone': '',
                'address': '',
                'bio': '',
                'avatar': image,
            })

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.avatar)
        self.assertIn('accounts/avatars/', user.avatar.name)
        self.assertTrue(user.avatar_url)
