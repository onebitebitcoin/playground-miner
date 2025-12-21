from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0073_alter_timecapsulebroadcastsetting_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sidebarconfig',
            name='show_compatibility',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='sidebarconfig',
            name='show_timecapsule',
            field=models.BooleanField(default=True),
        ),
    ]
