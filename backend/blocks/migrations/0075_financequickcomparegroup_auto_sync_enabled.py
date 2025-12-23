from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0074_sidebarconfig_show_compatibility_timecapsule'),
    ]

    operations = [
        migrations.AddField(
            model_name='financequickcomparegroup',
            name='auto_sync_enabled',
            field=models.BooleanField(
                default=True,
                help_text='자동 기본 자산 동기화를 유지할지 여부'
            ),
        ),
    ]
