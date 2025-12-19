from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0058_remove_compatibilityquickpreset_stored_saju'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compatibilityquickpreset',
            name='description',
        ),
    ]
