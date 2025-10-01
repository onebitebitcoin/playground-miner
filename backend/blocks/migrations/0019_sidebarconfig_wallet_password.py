from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0018_sidebarconfig_show_utxo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sidebarconfig',
            name='wallet_password_hash',
            field=models.CharField(default='', blank=True, max_length=128),
        ),
    ]

