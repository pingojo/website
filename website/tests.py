from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Company, Email, Role

class ApplicationAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')

    def test_create_application(self):
        url = reverse('application_view')
        data = {
            'company_name': 'Test Company',
            'role_title': 'Software Engineer',
            'applied_date': '2023-03-21',
            'salary_range': '80000-120000',
            'equity': 1.5,
            'gmail_id': 'GEbqgzGslkjhsxkbQKcfvWBQztRFpUIW',
            'from_email': 'email@test-user-test-email-test.com',
            'stage': 'Applied',
            'company_size': 50,
            'email_date': 'Thu, Mar 23, 2023, 12:57 PM',
            'location': 'San Francisco, CA',
            'founders': 'John Doe, Jane Smith',
            'benefits': 'Health insurance, 401k, stock options',
            'about': 'Test Company is a software development company.'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Role.objects.count(), 1)
        self.assertEqual(response.json()['total_applications'], 1)

        company = Company.objects.first()
        role = Role.objects.first()
        self.assertEqual(company.name, data['company_name'])
        self.assertEqual(role.title, data['role_title'])

        email = Email.objects.first()
        self.assertEqual(email.gmail_id, data['gmail_id'])
        

