from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Project, VolunteerHours, Announcement, Feedback, Message
from .models import VolunteerProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=[('volunteer', 'Volunteer'), ('organization', 'Organization')])  # Removed 'admin'
    skills = forms.CharField(max_length=255, required=False, help_text='Comma-separated list of skills')
    interests = forms.CharField(max_length=255, required=False, help_text='Comma-separated list of interests')
    availability = forms.CharField(max_length=100, required=False, help_text='Availability description')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type', 'skills', 'interests', 'availability']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = Profile.objects.create(user=user)
            if self.cleaned_data.get('user_type') == 'volunteer':
                profile.is_volunteer = True
                profile.save()
                VolunteerProfile.objects.create(
                    user=user,
                    skills=self.cleaned_data.get('skills'),
                    interests=self.cleaned_data.get('interests'),
                    availability=self.cleaned_data.get('availability')
                )
            elif self.cleaned_data.get('user_type') == 'organization':
                profile.is_organization = True
                profile.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    profile_picture = forms.ImageField(required=False)  # Add profile picture field

    class Meta:
        model = Profile
        fields = ['username', 'profile_picture', 'address', 'phone_number', 'organization_name']

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        # Set the initial value for the username field
        self.fields['username'].initial = self.instance.user.username

    def save(self, *args, **kwargs):
        # Update the related User object
        user = self.instance.user
        user.username = self.cleaned_data['username']
        user.save()
        return super(ProfileUpdateForm, self).save(*args, **kwargs)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'location', 'max_volunteers']
        
class VolunteerHoursForm(forms.ModelForm):
    class Meta:
        model = VolunteerHours
        fields = ['volunteer', 'project', 'hours']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(VolunteerHoursForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['volunteer'].queryset = User.objects.filter(profile__is_volunteer=True)
            self.fields['project'].queryset = Project.objects.filter(created_by=user)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['content']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'content']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MessageForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['receiver'].queryset = User.objects.exclude(id=user.id)

class VolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        fields = ['skills', 'interests', 'availability']
