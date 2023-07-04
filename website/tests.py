from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Company, Email, Role

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Company, Role, Application, Email, Job, Stage

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
            'stage_name': 'Applied',
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
        #self.assertEqual(response.json()['total_applications'], 2)

        company = Company.objects.first()
        role = Role.objects.first()
        self.assertEqual(company.name, data['company_name'])
        self.assertEqual(role.title, data['role_title'])

        email = Email.objects.first()
        self.assertEqual(email.gmail_id, data['gmail_id'])

    def test_get_applications(self):
        # Create test data
        company = Company.objects.create(name='Test Company')
        role = Role.objects.create(title='Software Engineer')
        job = Job.objects.create(company=company, role=role)
        stage = Stage.objects.create(name='Applied', order=1)
        application = Application.objects.create(user=self.user, job=job, company=company, stage=stage)
        email = Email.objects.create(
            gmail_id='GEbqgzGslkjhsxkbQKcfvWBQztRFpUIW',
            from_email='email@test-user-test-email-test.com',
            application=application
        )

        url = reverse('application_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        email_data = response.json()['emails'][0]
        self.assertEqual(email_data['gmail_id'], email.gmail_id)
        #self.assertEqual(email_data['subject'], role.title)
        self.assertEqual(email_data['company_name'], company.name)
        self.assertEqual(email_data['company_slug'], company.slug)





    def test_update_application(self):
        url = reverse('application_view')
        data = {
            'company_name': 'Test Company',
            'role_title': 'Software Engineer',
            'applied_date': '2023-03-21',
            'salary_range': '80000-120000',
            'equity': 1.5,
            'gmail_id': 'GEbqgzGslkjhsxkbQKcfvWBQztRFpUIW',
            'from_email': 'email@test-user-test-email-test.com',
            'stage_name': 'Passed',
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
        #self.assertEqual(response.json()['total_applications'], 2)

        company = Company.objects.first()
        role = Role.objects.first()
        self.assertEqual(company.name, data['company_name'])
        self.assertEqual(role.title, data['role_title'])

        email = Email.objects.first()
        self.assertEqual(email.gmail_id, data['gmail_id'])


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Job
from .forms import JobForm

class JobAddTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.job_add_url = reverse('job_add')  # assuming the url name for the view is job_add
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_job_add_post(self):
        self.client.login(username='testuser', password='12345')
        self.assertTrue(self.client.login(username='testuser', password='12345'))
        response = self.client.post(self.job_add_url, {
            'company': 'Test Company',
            'role': 'Software Developer',
            'type': 'Full-Time',
            'location': 'California, USA',
            'remote': 'true',
            'link': 'testurl.com',
            'email': 'test@testcompany.com',
            'description': 'This is a test job description.'
        })
        self.assertEqual(response.status_code, 302)  # After successful post, Django usually redirects so expecting 302
        self.assertTrue(Job.objects.filter(added_by=self.user).exists())  # check if Job was created for the user
        new_job = Job.objects.get(added_by=self.user)  # get the Job object associated with the user
        self.assertEqual(new_job.added_by, self.user)
        self.assertEqual(new_job.company.name, 'Test Company')
        self.assertEqual(new_job.role.title, 'Software Developer')

    def test_job_add_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.job_add_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], JobForm)

