from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0075_financequickcomparegroup_auto_sync_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='financequerylog',
            name='is_prefetch',
            field=models.BooleanField(default=False),
        ),
    ]

