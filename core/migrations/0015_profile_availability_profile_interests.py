# Generated by Django 4.2.13 on 2024-08-15 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_project_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='availability',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='interests',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
