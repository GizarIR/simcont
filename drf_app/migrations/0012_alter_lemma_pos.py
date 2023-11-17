# Generated by Django 4.2.5 on 2023-11-17 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drf_app', '0011_alter_lemma_pos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lemma',
            name='pos',
            field=models.CharField(choices=[('X', 'Other'), ('ADJ', 'Adjective'), ('ADP', 'adposition'), ('ADV', 'adverb'), ('AUX', 'auxiliary'), ('CCONJ', 'coordinating conjunction'), ('DET', 'determiner'), ('INTJ', 'interjection'), ('NOUN', 'noun'), ('NUM', 'numeral'), ('PART', 'particle'), ('PRON', 'pronoun'), ('PROPN', 'proper noun'), ('PUNCT', 'punctuation'), ('SCONJ', 'subordinating conjunction'), ('SYM', 'symbol'), ('SPACE', 'space'), ('VERB', 'verb')], default='X', max_length=7),
        ),
    ]
