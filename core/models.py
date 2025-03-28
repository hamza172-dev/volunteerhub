from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    is_volunteer = models.BooleanField(default=False)
    is_organization = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    address = models.CharField(max_length=255, blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    organization_name = models.CharField(max_length=255, blank=True, null=True)  
    availability = models.CharField(max_length=255, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class Project(models.Model):
    title = models.CharField(max_length=100, default='Default Title')
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    volunteers = models.ManyToManyField(User, related_name='projects')
    max_volunteers = models.PositiveIntegerField(default=10)
    location = models.CharField(max_length=255, null=True, blank=True)  # New field for location name
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.title

    def is_full(self):
        return self.volunteers.count() >= self.max_volunteers

    def is_starting_soon(self):
        return self.start_date <= timezone.now().date() + timedelta(days=3)

    def is_ending_soon(self):
        return self.end_date <= timezone.now().date() + timedelta(days=3)


class VolunteerHours(models.Model):
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    hours = models.PositiveIntegerField()
    date = models.DateField(null=True, blank=True)  # Allow null and blank values

    def __str__(self):
        return f"{self.volunteer.username} - {self.project.title}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Feedback(models.Model):
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.volunteer.username} on {self.project.title}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class VolunteerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    skills = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    availability = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"
