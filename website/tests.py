from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory

from .views import index


class SimpleTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_details(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        response = index(request)
        self.assertEqual(response.status_code, 200)
