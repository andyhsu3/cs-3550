# Generated by Django 5.1 on 2024-09-30 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='submission',
            name='score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
