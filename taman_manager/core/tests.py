from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, Task
from django.utils import timezone

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_signup_functionality(self):
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'firstname': 'Test',
            'lastname': 'User'
        })
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.full_name, 'Test User')

    def test_login_functionality(self):
        User.objects.create_user(username='loginuser', password='Password123!', email='login@example.com')
        response = self.client.post(self.login_url, {
            'username': 'loginuser',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

class TaskManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='taskuser', password='Password123!')
        self.client.login(username='taskuser', password='Password123!')
        self.dashboard_url = reverse('dashboard')
        self.create_task_url = reverse('create_task')
        self.view_tasks_url = reverse('view_tasks')

    def test_dashboard_metrics(self):
        Task.objects.create(name='Task 1', description='Desc 1', status='Created', category='Work', created_by=self.user)
        Task.objects.create(name='Task 2', description='Desc 2', status='Completed', category='Personal', created_by=self.user, completed_at=timezone.now())
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.context['total_tasks'], 2)
        self.assertEqual(response.context['completed_tasks'], 1)
        self.assertEqual(response.context['pending_tasks'], 1)

    def test_task_crud(self):
        # Create
        response = self.client.post(self.create_task_url, {
            'name': 'New Task',
            'description': 'Description',
            'category': 'Work',
            'status': 'Created',
            'milestone': 'M1'
        })
        self.assertRedirects(response, self.view_tasks_url)
        self.assertEqual(Task.objects.filter(name='New Task').count(), 1)
        
        task = Task.objects.get(name='New Task')
        
        # Edit
        edit_url = reverse('edit_task', args=[task.id])
        response = self.client.post(edit_url, {
            'name': 'Updated Task',
            'description': 'Updated Desc',
            'category': 'Personal',
            'status': 'In Progress',
            'milestone': 'M2'
        })
        task.refresh_from_db()
        self.assertEqual(task.name, 'Updated Task')
        
        # Delete
        delete_url = reverse('delete_task', args=[task.id])
        # First GET should show confirmation page
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        # POST should delete
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.view_tasks_url)
        self.assertEqual(Task.objects.filter(id=task.id).count(), 0)

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='Password123!')
        self.profile = Profile.objects.get_or_create(user=self.user)[0]
        self.client.login(username='profileuser', password='Password123!')
        self.view_profile_url = reverse('view_profile')
        self.edit_profile_url = reverse('profile')

    def test_profile_read_update(self):
        # ... (same as before)
        response = self.client.get(self.view_profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Update
        response = self.client.post(self.edit_profile_url, {
            'full_name': 'New Name',
            'email': 'new@example.com',
            'bio': 'My bio',
            'location': 'New York'
        })
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'New Name')

    def test_delete_account(self):
        delete_url = reverse('delete_account')
        # GET should show confirmation
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        # POST should delete
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(User.objects.filter(username='profileuser').count(), 0)

class APITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='Password123!')
        self.client.login(username='apiuser', password='Password123!')
        self.analytics_url = reverse('analytics_api')

    def test_analytics_api(self):
        Task.objects.create(name='T1', status='Completed', category='Work', created_by=self.user, completed_at=timezone.now())
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('weekly_data', data)
        self.assertIn('category_data', data)

class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='resetuser', password='OldPassword123!', email='reset@example.com')
        self.forgot_url = reverse('forgot-password')

    def test_password_reset_flow(self):
        # 1. Forgot password request
        response = self.client.post(self.forgot_url, {'email': 'reset@example.com'})
        from .models import PasswordReset
        self.assertEqual(PasswordReset.objects.filter(user=self.user).count(), 1)
        reset_obj = PasswordReset.objects.get(user=self.user)
        
        # 2. Reset sent page
        sent_url = reverse('password-reset-sent', args=[reset_obj.reset_id])
        response = self.client.get(sent_url)
        self.assertEqual(response.status_code, 200)
        
        # 3. Reset password
        reset_url = reverse('reset-password', args=[reset_obj.reset_id])
        response = self.client.post(reset_url, {
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertRedirects(response, reverse('login'))
        
        # 4. Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
