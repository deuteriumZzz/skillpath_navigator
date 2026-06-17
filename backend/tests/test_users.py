from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTestCase(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "carol",
                "email": "carol@example.com",
                "password": "pass12345",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="carol").exists())

        response = self.client.post(
            "/api/v1/auth/token/", {"username": "carol", "password": "pass12345"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
