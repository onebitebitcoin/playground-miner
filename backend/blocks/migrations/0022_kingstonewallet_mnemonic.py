from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0021_kingstonewallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='kingstonewallet',
            name='mnemonic',
            field=models.CharField(blank=True, default='', max_length=512),
        ),
    ]

