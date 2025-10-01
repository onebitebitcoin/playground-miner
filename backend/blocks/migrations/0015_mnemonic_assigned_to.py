from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0014_mnemonic_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='mnemonic',
            name='assigned_to',
            field=models.CharField(max_length=64, blank=True, null=True),
        ),
    ]

