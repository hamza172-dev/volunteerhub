# Generated by Django 4.2.13 on 2024-08-13 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_project_is_featured'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='is_featured',
        ),
        migrations.AddField(
            model_name='project',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
