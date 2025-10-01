from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0019_sidebarconfig_wallet_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='sidebarconfig',
            name='wallet_password_plain',
            field=models.CharField(default='', blank=True, max_length=128),
        ),
    ]

