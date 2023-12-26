# Generated by Django 4.2.5 on 2023-12-26 10:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import drf_app.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drf_app', '0011_lemma_translate_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time_create', models.DateTimeField(auto_now_add=True)),
                ('time_update', models.DateTimeField(auto_now=True)),
                ('is_finished', models.BooleanField(default=False)),
                ('learner', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('vocabulary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drf_app.vocabulary')),
            ],
        ),
        migrations.CreateModel(
            name='EducationLemma',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('NEW', 'new'), ('ON_STUDY', 'on_study'), ('LEARNER', 'learned')], default='NEW', max_length=8)),
                ('throughEducation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drf_app.education')),
                ('throughLemma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drf_app.lemma')),
            ],
        ),
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('limit_lemmas_item', models.PositiveIntegerField(default=2)),
                ('limit_lemmas_period', models.PositiveIntegerField(default=7)),
                ('set_lemmas', models.JSONField(blank=True, default=None, null=True, validators=[drf_app.validators.validate_json])),
                ('education', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drf_app.education')),
            ],
        ),
    ]
