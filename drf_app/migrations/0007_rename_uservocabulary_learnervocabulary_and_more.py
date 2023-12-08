# Generated by Django 4.2.5 on 2023-12-08 13:15

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drf_app', '0006_rename_studentvocabulary_uservocabulary_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserVocabulary',
            new_name='LearnerVocabulary',
        ),
        migrations.RenameField(
            model_name='learnervocabulary',
            old_name='throughUser',
            new_name='throughLearner',
        ),
        migrations.RemoveField(
            model_name='vocabulary',
            name='users',
        ),
        migrations.AddField(
            model_name='vocabulary',
            name='learners',
            field=models.ManyToManyField(related_name='voc_learner', through='drf_app.LearnerVocabulary', to=settings.AUTH_USER_MODEL),
        ),
    ]
