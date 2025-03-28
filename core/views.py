from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone  # Ensure this is imported
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Profile, Project, VolunteerHours, Announcement, Feedback, Message, Notification, VolunteerProfile
from .forms import MessageForm, UserRegisterForm, ProfileUpdateForm, ProjectForm, VolunteerHoursForm, FeedbackForm, AnnouncementForm
import pandas as pd
import plotly.express as px
from django.db import models  # Add this import
import joblib
from django.core.mail import send_mail
from datetime import timedelta
from django.conf import settings
import os
import requests
from django.db.models import Sum, Count
from django.db.models.signals import pre_save
from django.dispatch import receiver
from geopy.geocoders import Nominatim
from .models import Project
from django.contrib import messages
from .forms import VolunteerProfileForm
from django.db import IntegrityError ,transaction
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models.signals import post_save
from .forms import UserRegisterForm
from .models import Profile, VolunteerProfile
from .signals import create_or_update_user_profile




# Notification function
def notify_user(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}", {
            'type': 'notification_message',
            'message': message
        }
    )
    user = get_object_or_404(User, pk=user_id)
    Notification.objects.create(user=user, message=message)

def home(request):
    # Featured projects should include only ongoing projects
    featured_projects = Project.objects.filter(end_date__gte=timezone.now().date())[:3]

    # Calculate unread messages count for the logged-in user
    unread_messages_count = 0
    if request.user.is_authenticated:  # Check if the user is logged in
        unread_messages_count = request.user.received_messages.filter(is_read=False).count()

    # Impact statistics
    total_projects = Project.objects.count()
    total_volunteers = VolunteerHours.objects.values('volunteer').distinct().count()
    total_hours = VolunteerHours.objects.aggregate(Sum('hours'))['hours__sum'] or 0

    # Prepare project locations for the map
    project_locations = list(Project.objects.values('title', 'latitude', 'longitude'))

    # Context to pass to the template
    context = {
        'featured_projects': featured_projects,
        'total_projects': total_projects,
        'total_volunteers': total_volunteers,
        'total_hours': total_hours,
        'project_locations': project_locations,
        'unread_messages_count': unread_messages_count,  # Add this to context
    }

    return render(request, 'core/home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Temporarily disconnect the post_save signal for User
                    post_save.disconnect(create_or_update_user_profile, sender=User)

                    user = form.save()
                    user_type = form.cleaned_data.get('user_type')
                    
                    # Reconnect the signal
                    post_save.connect(create_or_update_user_profile, sender=User)
                    
                    # Check if a Profile already exists
                    profile, created = Profile.objects.get_or_create(user=user)
                    if created:
                        print(f"Profile created for user: {user.username}")
                    else:
                        print(f"Profile already exists for user: {user.username}")

                    # Set profile attributes based on user type
                    if user_type == 'volunteer':
                        profile.is_volunteer = True
                        VolunteerProfile.objects.get_or_create(
                            user=user,
                            defaults={'skills': "", 'interests': "", 'availability': ""}
                        )
                    elif user_type == 'organization':
                        profile.is_organization = True
                    elif user_type == 'admin':
                        profile.is_admin = True

                    profile.save()

                    # Add success message
                    messages.success(request, "Account created successfully! Please log in.")

                    # Redirect to login page
                    return redirect('login')

            except IntegrityError as e:
                print(f"IntegrityError occurred: {e}")
                form.add_error(None, 'A profile already exists for this user.')
            finally:
                # Ensure the signal is reconnected
                post_save.connect(create_or_update_user_profile, sender=User)
        else:
            print("Form is invalid:", form.errors)
    else:
        form = UserRegisterForm()

    return render(request, 'core/register.html', {'form': form})




def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                notify_user(user.id, "You have successfully logged in!")
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')

@login_required
def profile(request):
    # Handle both forms for Profile and VolunteerProfile
    if request.method == 'POST':
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        vp_form = VolunteerProfileForm(request.POST, instance=getattr(request.user, 'volunteerprofile', None))

        if p_form.is_valid() and vp_form.is_valid():
            p_form.save()
            vp_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')

    else:
        # Load data into both forms
        p_form = ProfileUpdateForm(instance=request.user.profile)
        vp_form = VolunteerProfileForm(instance=getattr(request.user, 'volunteerprofile', None))

    context = {
        'p_form': p_form,
        'vp_form': vp_form,
    }

    return render(request, 'core/profile.html', context)

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            notify_user(request.user.id, "Your project has been created.")
            return redirect('dashboard_organization')
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'creating': True  # Add a context variable to indicate creation
    }
    return render(request, 'core/project_form.html', context)



@login_required
def project_list(request):
    try:
        today = timezone.now().date()
        available_projects = Project.objects.filter(end_date__gte=today)
        previous_projects = Project.objects.filter(end_date__lt=today)
        return render(request, 'core/project_list.html', {
            'available_projects': available_projects,
            'previous_projects': previous_projects
        })
    except Exception as e:
        logger.error(f"Error in project_list view: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('home')  # Redirect to home or any other fallback view
    

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    volunteers = project.volunteers.all()
    is_volunteered = request.user in volunteers
    is_organization_or_admin = request.user.profile.is_organization or request.user.profile.is_admin
    return render(request, 'core/project_detail.html', {
        'project': project,
        'volunteers': volunteers,
        'is_volunteered': is_volunteered,
        'is_organization_or_admin': is_organization_or_admin
    })

@login_required
def volunteer_for_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Prevent organizations from signing up for projects
    if request.user.profile.is_organization:
        messages.error(request, "Organizations cannot sign up for projects.")
        return redirect('project_detail', pk=pk)
    
    # Prevents admins or non-volunteers from signing up as well
    if not request.user.profile.is_volunteer:
        messages.error(request, "Only volunteers can sign up for projects.")
        return redirect('project_detail', pk=pk)

    if project.is_full():
        return render(request, 'core/project_detail.html', {'project': project, 'error': 'This project is already full.'})

    if request.method == 'POST':
        project.volunteers.add(request.user)
        return redirect('project_detail', pk=pk)

    return render(request, 'core/project_detail.html', {'project': project})

@login_required
def remove_volunteer_from_project(request, project_id, volunteer_id):
    project = get_object_or_404(Project, id=project_id)
    volunteer = get_object_or_404(User, id=volunteer_id)

    # Check if the project has ended
    if project.end_date < timezone.now().date():
        messages.error(request, "You cannot remove volunteers from a project that has ended.")
        return redirect('project_detail', pk=project_id)

    # Allow removal if the project has not ended
    if request.user == volunteer or request.user == project.created_by or request.user.profile.is_admin:
        project.volunteers.remove(volunteer)
        messages.success(request, f"{volunteer.username} has been removed from the project.")
    
    return redirect('project_detail', pk=project_id)


@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.completed = True
    project.save()
    for volunteer in project.volunteers.all():
        notify_user(volunteer.id, f"The project {project.title} has been completed!")
    return redirect('dashboard_organization')

from django.shortcuts import get_object_or_404

@login_required
def log_volunteer_hours(request, project_id):
    # Ensure the logged-in user is an organization
    if not request.user.profile.is_organization:
        return redirect('home')

    # Fetch the project by ID and ensure it belongs to the logged-in organization
    project = get_object_or_404(Project, id=project_id, created_by=request.user)

    if request.method == 'POST':
        form = VolunteerHoursForm(request.POST, user=request.user)
        if form.is_valid():
            volunteer_hours = form.save(commit=False)
            volunteer_hours.project = project  # Assign the project to the hours
            volunteer_hours.date = project.start_date  # Set the default date
            volunteer_hours.save()
            # Notify the volunteer
            notify_user(
                volunteer_hours.volunteer.id,
                f"Your hours for the project {project.title} have been logged."
            )
            return redirect('dashboard_organization')
    else:
        # Pass the user and restrict the form to this project's volunteers
        form = VolunteerHoursForm(user=request.user)

    return render(request, 'core/volunteer_hours_form.html', {'form': form, 'project': project})


@login_required
def dashboard_volunteer(request):
    today = now().date()

    # Fetch all projects the volunteer is involved in
    volunteer_projects = Project.objects.filter(volunteers=request.user)

    # Separate projects into upcoming and previous
    upcoming_projects = volunteer_projects.filter(end_date__gte=today)
    previous_projects = volunteer_projects.filter(end_date__lt=today)

    # Add feedback information to previous projects
    previous_projects_with_feedback = []
    for project in previous_projects:
        has_feedback = Feedback.objects.filter(project=project, volunteer=request.user).exists()
        previous_projects_with_feedback.append({'project': project, 'has_feedback': has_feedback})

    # Fetch volunteer hours
    volunteer_hours = VolunteerHours.objects.filter(volunteer=request.user)

    # Fetch volunteer feedback
    volunteer_feedback = Feedback.objects.filter(volunteer=request.user)

    context = {
        'upcoming_projects': upcoming_projects,
        'previous_projects_with_feedback': previous_projects_with_feedback,
        'volunteer_hours': volunteer_hours,
        'volunteer_feedback': volunteer_feedback,
        'today': today,
    }

    return render(request, 'core/dashboard_volunteer.html', context)



@login_required
def dashboard_organization(request):
    if not request.user.profile.is_organization:
        return redirect('home')

    organization_projects = Project.objects.filter(created_by=request.user)
    feedback_data = Feedback.objects.filter(project__in=organization_projects)
    log_hours_form = VolunteerHoursForm(user=request.user)

    context = {
        'organization_projects': organization_projects,
        'feedback_data': feedback_data,
        'log_hours_form': log_hours_form,
        'today': timezone.now().date()  # Pass today's date to the template
    }
    return render(request, 'core/dashboard_organization.html', context)

@login_required
def dashboard_admin(request):
    projects = Project.objects.all()
    volunteers = User.objects.filter(profile__is_volunteer=True)
    announcements = Announcement.objects.all()
    context = {
        'projects': projects,
        'volunteers': volunteers,
        'announcements': announcements,
    }
    return render(request, 'core/dashboard_admin.html', context)

@login_required
def post_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            notify_user(request.user.id, "Your announcement has been posted.")
            return redirect('dashboard_admin')
    else:
        form = AnnouncementForm()
    return render(request, 'core/announcement_form.html', {'form': form})

@login_required
def submit_feedback(request):
    project_id = request.GET.get('project_id')
    project = get_object_or_404(Project, id=project_id)

    # Prevent feedback submission for ongoing projects
    if project.end_date >= now().date():
        return redirect('dashboard_volunteer')  # Redirect if project is ongoing

    # Check if feedback already exists for this project by this user
    if Feedback.objects.filter(project=project, volunteer=request.user).exists():
        return redirect('dashboard_volunteer')  # Prevent duplicate feedback

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.volunteer = request.user
            feedback.project = project
            feedback.save()
            return redirect('dashboard_volunteer')
    else:
        form = FeedbackForm()

    return render(request, 'core/feedback_form.html', {'form': form, 'project': project})

@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if the current date is past the project's end date
    if timezone.now().date() > project.end_date:
        return redirect('dashboard_organization')  # Redirect if the project end date has passed
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            notify_user(request.user.id, f"The project {project.title} has been updated.")
            return redirect('dashboard_organization')
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'project': project,
        'today': timezone.now().date(),
        'creating': False  # Add a context variable to indicate editing
    }
    return render(request, 'core/project_form.html', context)

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    notify_user(request.user.id, f"The project {project.title} has been deleted.")
    return redirect('dashboard_admin')

@login_required
def get_project_date(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return JsonResponse({'start_date': project.start_date})


@login_required
def calendar_data(request):
    projects = Project.objects.all()
    events = []
    for project in projects:
        days_left = (project.end_date - timezone.now().date()).days
        events.append({
            'title': project.title + ' (Start)',
            'start': project.start_date.isoformat(),
            'description': project.description,
            'id': project.id,
            'daysLeft': days_left,  # Use camelCase for consistency with JavaScript
            'isStartSoon': project.is_starting_soon(),  # Use camelCase for consistency
            'isEndSoon': project.is_ending_soon(),      # Use camelCase for consistency
            'url': f'/projects/{project.id}/',          # Corrected URL pattern
        })
        events.append({
            'title': project.title + ' (End)',
            'start': project.end_date.isoformat(),
            'description': project.description,
            'id': project.id,
            'daysLeft': days_left,  # Use camelCase for consistency with JavaScript
            'isStartSoon': project.is_starting_soon(),  # Use camelCase for consistency
            'isEndSoon': project.is_ending_soon(),      # Use camelCase for consistency
            'url': f'/projects/{project.id}/',          # Corrected URL pattern
        })
    return JsonResponse(events, safe=False)

@login_required
def calendar(request):
    try:
        return render(request, 'core/calendar.html')
    except Exception as e:
        # Log the error if necessary
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('home')  # Redirect to home or any other fallback view


@login_required
def inbox(request):
    # Get all received messages for the user
    messages = request.user.received_messages.all()

    # Pass messages to the template
    return render(request, 'core/inbox.html', {'messages': messages})

@login_required
def view_message(request, pk):
    # Get the message
    message = get_object_or_404(Message, pk=pk)

    # Ensure the logged-in user is the recipient
    if message.receiver != request.user:
        return redirect('inbox')

    # Mark the message as read
    if not message.is_read:
        message.is_read = True
        message.save()

    # Render the message detail template
    return render(request, 'core/message_detail.html', {'message': message})

@login_required
def sent_messages(request):
    sent_messages = request.user.sent_messages.all()
    return render(request, 'core/sent_messages.html', {'messages': sent_messages})

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            notify_user(message.receiver.id, f"You have received a new message from {request.user.username}.")
            return redirect('inbox')
    else:
        form = MessageForm(user=request.user)
    return render(request, 'core/send_message.html', {'form': form})

@login_required
def view_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if message.receiver == request.user or message.sender == request.user:
        if message.receiver == request.user:
            message.is_read = True
            message.save()

        if request.method == 'POST':
            form = MessageForm(request.POST, user=request.user)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.sender = request.user
                reply.receiver = message.sender if message.receiver == request.user else message.receiver
                reply.save()
                notify_user(reply.receiver.id, f"You have received a reply from {request.user.username}.")
                return redirect('view_message', pk=reply.pk)
        else:
            initial_data = {
                'receiver': message.sender if message.receiver == request.user else message.receiver,
                'subject': f'Re: {message.subject}',
            }
            form = MessageForm(initial=initial_data, user=request.user)

        return render(request, 'core/view_message.html', {'message': message, 'form': form})
    else:
        return redirect('inbox')

@login_required
def notifications(request):
    notifications = request.user.notifications.filter(is_read=False)
    return render(request, 'core/notifications.html', {'notifications': notifications})

@login_required
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if notification.user == request.user:
        notification.is_read = True
        notification.save()
    return redirect('notifications')

from django.shortcuts import render
from django.db.models import Count
from django.utils.timezone import now

def analytics(request):
    # Metrics for KPI cards
    total_hours = VolunteerHours.objects.aggregate(Sum('hours'))['hours__sum'] or 0
    total_projects = Project.objects.count()
    ongoing_projects = Project.objects.filter(end_date__gte=now()).count()
    completed_projects = Project.objects.filter(end_date__lt=now()).count()

    # Project completion status with counts
    project_status = {
        "labels": ["Ongoing", "Completed"],
        "data": [ongoing_projects, completed_projects],
        "details": {
            "total_projects": total_projects,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
        }
    }

    # Context for template
    context = {
        "metrics": {
            "total_hours": total_hours,
            "total_projects": total_projects,
            "ongoing_projects": ongoing_projects,
        },
        "project_status": project_status,
    }

    return render(request, "core/analytics.html", context)





import re
@login_required
def recommend_projects(request):
    user = request.user

    # Ensure the user is a volunteer
    if not user.profile.is_volunteer:
        return redirect('home')

    # Get the volunteer's profile
    volunteer_profile = get_object_or_404(VolunteerProfile, user=user)

    # Fetch all ongoing projects (exclude already joined)
    projects = Project.objects.filter(end_date__gte=timezone.now().date()).exclude(volunteers=user)

    # Prepare volunteer's raw keywords (remove spaces, commas, etc.)
    def prepare_keywords(text):
        return set(re.sub(r'\W+', '', word.lower()) for word in text.split() if word.strip())

    volunteer_keywords = (
        prepare_keywords(volunteer_profile.skills) |
        prepare_keywords(volunteer_profile.interests) |
        prepare_keywords(volunteer_profile.availability)
    )

    recommended_projects = []

    for project in projects:
        # Prepare raw keywords from project description
        project_keywords = prepare_keywords(project.description)

        # Calculate intersection of volunteer keywords and project keywords
        matching_keywords = volunteer_keywords & project_keywords
        match_score = len(matching_keywords)  # Use the number of matches as the score

        if match_score > 0:
            recommended_projects.append({
                'project': project,
                'match_score': match_score,
                'matching_keywords': list(matching_keywords),  # Optional: Display matched words
            })

    # Sort projects by match score (highest first)
    recommended_projects = sorted(recommended_projects, key=lambda x: x['match_score'], reverse=True)

    return render(request, 'core/recommend_projects.html', {
        'recommended_projects': [rec['project'] for rec in recommended_projects],
        'recommendations_with_details': recommended_projects  # For debugging or advanced templates
    })


