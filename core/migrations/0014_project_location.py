# Generated by Django 4.2.13 on 2024-08-13 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_remove_project_is_featured_project_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
