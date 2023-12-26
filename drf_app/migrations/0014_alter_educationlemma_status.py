# Generated by Django 4.2.5 on 2023-12-26 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drf_app', '0013_lemma_educations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationlemma',
            name='status',
            field=models.CharField(choices=[('NE', 'New'), ('ST', 'On_study'), ('LE', 'Learned')], default='NE', max_length=2),
        ),
    ]
