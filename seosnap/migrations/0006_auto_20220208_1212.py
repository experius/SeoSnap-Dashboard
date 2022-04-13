# Generated by Django 3.1.12 on 2022-02-08 12:12

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('seosnap', '0005_auto_20210214_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='website',
            name='notification_email',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='website',
            name='notification_sent_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]