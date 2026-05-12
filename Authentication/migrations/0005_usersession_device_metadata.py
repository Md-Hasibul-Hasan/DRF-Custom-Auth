from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0004_increase_otp_hash_field_lengths'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersession',
            name='browser',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='device_fingerprint',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='device_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='operating_system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
