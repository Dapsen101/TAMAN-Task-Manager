
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, default=1)
    email = models.EmailField(default=1)  # Adding the email field
    location = models.CharField(max_length=100, blank=True, null=True)  # Adding the location field
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', default='ProfilePicture.png')
 
    def __str__(self):
        return f'{self.user.username} Profile' 
    
class Task(models.Model):
    STATUS_CHOICES = [
        ('Created', 'Created'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Created')
    milestone = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name