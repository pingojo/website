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
            'job_type': 'Full-Time',
            'location': 'California, USA',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'USA',
            'remote': True,
            'link': 'testurl.com',
            'email': 'test@testcompany.com',
            'description': 'This is a test job description.'
        })
        self.assertEqual(response.status_code, 302)  # After successful post, Django usually redirects so expecting 302
        self.assertTrue(Job.objects.filter(added_by=self.user).exists())  # check if Job was created for the user
        new_job = Job.objects.get(added_by=self.user)  # get the Job object associated with the user
        self.assertEqual(new_job.added_by, self.user)
        self.assertEqual(new_job.company.name, 'Test Company')
        self.assertEqual(new_job.company.city, 'San Francisco')
        self.assertEqual(new_job.company.state, 'CA')
        self.assertEqual(new_job.company.country, 'USA')
        self.assertEqual(new_job.remote, True)
        self.assertEqual(new_job.role.title, 'Software Developer')

    def test_job_add_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.job_add_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], JobForm)



# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import unittest

# class JobAddFrontendTestCase(unittest.TestCase):
#     def setUp(self):
#         self.driver = webdriver.Firefox()  # You can use any browser driver you want
#         self.driver.get('http://localhost:8000/login')  # Assuming your Django project is running on localhost:8000 and has a login page
#         self.driver.find_element(By.NAME, "username").send_keys('testuser')
#         self.driver.find_element(By.NAME, "password").send_keys('12345' + Keys.RETURN)
#         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "userMenu")))  # assuming there is a user menu appearing after login

#     def test_job_add(self):
#         self.driver.get('http://localhost:8000/job_add')  # replace with your job_add URL
#         self.driver.find_element(By.NAME, "company").send_keys('Test Company')
#         self.driver.find_element(By.NAME, "role").send_keys('Software Developer')
#         # Continue the above for all the form fields
#         self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()
#         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "jobList")))
#         jobList = self.driver.find_element(By.ID, "jobList").text  # assuming jobs are listed in an element with id 'jobList'
#         self.assertIn('Test Company', jobList)
#         self.assertIn('Software Developer', jobList)
#         # Continue the above assertions for all the job fields

#     def tearDown(self):
#         self.driver.quit()

# if __name__ == "__main__":
#     unittest.main()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Job, Role, Company  # assuming these are the names of your models
from django.urls import reverse

class AddJobLinkTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.add_job_link_url = reverse('add_job_view')  
        self.role = Role.objects.create(title="Software Developer")
        self.company = Company.objects.create(name="Test Company")

    def test_add_job_link(self):
        data = {
            'company': self.company.name,
            'title': self.role.title,
            'datePosted': '2023-07-05',
            'salaryRange': '$50000-$60000',
            'CompanySalary': '',
            'location': 'California, USA',
            'website': 'testurl.com',
            'CompanyAddress': 'USA',
            'CompanyStatus': 'Active',
            'CompanyRemote': 'Yes',
            'CompanyPhone': '1234567890',
            'CompanyEmail': 'test@testcompany.com',
            'link': 'https://testurl.com'
        }

        response = self.client.post(self.add_job_link_url, data, format='json')
        self.assertEqual(response.status_code, 200)  # Checking that the request was processed successfully
        self.assertTrue(Job.objects.filter(company=self.company, role=self.role).exists())  # Checking that a job was created
        new_job = Job.objects.get(company=self.company, role=self.role)
        self.assertEqual(new_job.posted_date.strftime('%Y-%m-%d'), data['datePosted'])
        self.assertEqual(new_job.salary_min, 50000)
        self.assertEqual(new_job.salary_max, 60000)
        self.assertEqual(new_job.link, data['link'])
        self.assertEqual(new_job.location, data['location'])
        self.assertEqual(new_job.job_type, data['CompanyStatus'])

        # Testing the remaining data items
        new_company = Company.objects.get(name=data['company'])
        self.assertEqual(new_company.website, data['website'])
        self.assertEqual(new_company.email, data['CompanyEmail'])
        self.assertEqual(new_company.phone, data['CompanyPhone'])

        # Assume that 'remote' field is a boolean in the Job model
        self.assertEqual(new_job.remote, True if data['CompanyRemote'] == 'Yes' else False)

        # Validate the response data
        self.assertIn('applications', response.json())
