# Generated by Django 4.2.5 on 2023-11-03 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drf_app', '0005_alter_vocabulary_order_lemmas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vocabulary',
            name='order_lemmas',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]