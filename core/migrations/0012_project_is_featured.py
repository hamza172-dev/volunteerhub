# Generated by Django 4.2.13 on 2024-08-13 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_volunteerprofile_availability_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
    ]
