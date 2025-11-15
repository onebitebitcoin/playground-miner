from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0026_route_event_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='fee_fixed_currency',
            field=models.CharField(choices=[('BTC', 'BTC'), ('USDT', 'USDT')], default='BTC', max_length=10),
        ),
    ]

