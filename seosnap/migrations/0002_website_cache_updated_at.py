# Generated by Django 3.0.2 on 2020-01-30 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seosnap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='cache_updated_at',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]