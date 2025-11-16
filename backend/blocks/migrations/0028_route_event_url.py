from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0027_route_fee_fixed_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='event_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
