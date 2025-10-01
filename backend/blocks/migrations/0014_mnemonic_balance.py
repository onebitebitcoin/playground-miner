from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0013_routingsnapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='mnemonic',
            name='balance_sats',
            field=models.BigIntegerField(default=0),
        ),
    ]

