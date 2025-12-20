from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0071_merge_20251219_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='timecapsule',
            name='broadcast_txid',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='timecapsule',
            name='broadcasted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
