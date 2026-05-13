from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0005_usersession_device_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pending_email_otp_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='pending_email_otp_locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
