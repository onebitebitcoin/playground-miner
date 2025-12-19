from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0060_add_saylor_quick_preset'),
    ]

    operations = [
        migrations.AddField(
            model_name='compatibilityquickpreset',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
