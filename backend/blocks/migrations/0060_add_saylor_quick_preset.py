from django.db import migrations
from datetime import datetime


def ensure_saylor_preset(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')
    Preset.objects.get_or_create(
        label='마이클 세일러',
        defaults={
            'birthdate': datetime(1965, 2, 4).date(),
            'gender': 'male',
            'description': 'MicroStrategy CEO이자 비트코인 트리플 맥시.',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Michael_Saylor_2016.jpg/640px-Michael_Saylor_2016.jpg',
            'sort_order': 1,
            'is_active': True,
        }
    )


def noop_reverse(apps, schema_editor):
    # No-op to avoid deleting reinstated data.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0059_remove_compatibilityquickpreset_description'),
    ]

    operations = [
        migrations.RunPython(ensure_saylor_preset, noop_reverse),
    ]
