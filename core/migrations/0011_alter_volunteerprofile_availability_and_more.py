# Generated by Django 4.2.13 on 2024-08-04 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_volunteerprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volunteerprofile',
            name='availability',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='volunteerprofile',
            name='interests',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='volunteerprofile',
            name='skills',
            field=models.TextField(blank=True),
        ),
    ]
