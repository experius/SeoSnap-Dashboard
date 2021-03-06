# Generated by Django 3.0.7 on 2021-02-14 15:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('seosnap', '0004_create_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='notification_cooldown',
            field=models.IntegerField(default=3600),
        ),
        migrations.AddField(
            model_name='website',
            name='notification_email',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='website',
            name='notification_failure_rate',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='website',
            name='notification_sent_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
