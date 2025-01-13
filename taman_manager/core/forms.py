from django import forms
from .models import Profile
from .models import Task

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'email', 'location', 'bio', 'image']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'milestone', 'description', 'assigned_to', 'status']
        widgets = {
            'status': forms.Select(choices=[
                ('Created', 'Created'),
                ('In Progress', 'In Progress'),
                ('Completed', 'Completed'),
                ('Ongoing', 'Ongoing'),
            ]),
        }