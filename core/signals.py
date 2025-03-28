from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from geopy.geocoders import Nominatim
from .models import Project, Profile, VolunteerProfile
from django.contrib.auth.models import User

@receiver(pre_save, sender=Project)
def geocode_location(sender, instance, **kwargs):
    if instance.location and not (instance.latitude and instance.longitude):
        geolocator = Nominatim(user_agent="volunteer_hub")
        location = geolocator.geocode(instance.location)
        if location:
            instance.latitude = location.latitude
            instance.longitude = location.longitude

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, profile_created = Profile.objects.get_or_create(user=instance)
        if profile.is_volunteer:
            VolunteerProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        if instance.profile.is_volunteer:
            VolunteerProfile.objects.get_or_create(user=instance)
