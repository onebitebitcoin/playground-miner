from django.db import migrations
from datetime import datetime


def add_vitalik_remove_bitcoin(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')

    # 비트코인 제거
    Preset.objects.filter(label='비트코인').delete()

    # 비탈릭 부테린 추가
    Preset.objects.get_or_create(
        label='비탈릭 부테린',
        defaults={
            'birthdate': datetime(1994, 1, 31).date(),
            'gender': 'male',
            'description': '이더리움 창시자이자 크립토 철학자.',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg/640px-Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg',
            'sort_order': 5,
            'is_active': True,
        }
    )


def reverse_changes(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')

    # 비탈릭 부테린 제거
    Preset.objects.filter(label='비탈릭 부테린').delete()

    # 비트코인 복원
    Preset.objects.get_or_create(
        label='비트코인',
        defaults={
            'birthdate': datetime(2009, 1, 4).date(),
            'gender': '',
            'description': '제네시스 블록 명식으로 궁합을 즉시 계산합니다.',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/4/46/Bitcoin.svg',
            'sort_order': 0,
            'is_active': True,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0048_update_compatibility_model_default'),
    ]

    operations = [
        migrations.RunPython(add_vitalik_remove_bitcoin, reverse_changes),
    ]
