from django.db import migrations, models


DEFAULT_DESCRIPTIONS = {
    '마이클 세일러': 'MicroStrategy CEO이자 비트코인 트리플 맥시.',
    '도널드 트럼프': '전 미 대통령으로 친비트코인 행보를 강화 중.',
    '래리 핑크': '블랙록 CEO, 기관 비트코인 수요를 이끄는 인물.',
    '제이미 다이먼': 'JP모건 CEO, 비판과 도입을 오가는 상징적 인물.',
}


def seed_descriptions(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')
    for label, desc in DEFAULT_DESCRIPTIONS.items():
        Preset.objects.filter(label=label, description='').update(description=desc)


def remove_descriptions(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')
    Preset.objects.filter(label__in=DEFAULT_DESCRIPTIONS.keys()).update(description='')


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0044_compatibilityquickpreset'),
    ]

    operations = [
        migrations.AddField(
            model_name='compatibilityquickpreset',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.RunPython(seed_descriptions, remove_descriptions),
    ]
