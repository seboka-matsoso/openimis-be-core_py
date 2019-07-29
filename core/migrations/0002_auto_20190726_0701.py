# Generated by Django 2.1.9 on 2019-07-26 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='moduleconfiguration',
            name='is_disabled_until',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='moduleconfiguration',
            name='is_exposed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='moduleconfiguration',
            name='layer',
            field=models.CharField(choices=[('fe', 'frontend'), ('be', 'backend')], default='be', max_length=2),
        ),
    ]
