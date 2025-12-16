from django.db import migrations, models
from datetime import datetime


def seed_presets(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')
    defaults = [
        {
            'label': '마이클 세일러',
            'birthdate': datetime(1965, 2, 4).date(),
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Michael_Saylor_2016.jpg/640px-Michael_Saylor_2016.jpg',
            'sort_order': 1,
        },
        {
            'label': '도널드 트럼프',
            'birthdate': datetime(1946, 6, 14).date(),
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/640px-Donald_Trump_official_portrait.jpg',
            'sort_order': 2,
        },
        {
            'label': '래리 핑크',
            'birthdate': datetime(1952, 11, 2).date(),
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Laurence_D._Fink.jpg/640px-Laurence_D._Fink.jpg',
            'sort_order': 3,
        },
        {
            'label': '제이미 다이먼',
            'birthdate': datetime(1956, 3, 13).date(),
            'gender': 'male',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Jamie_Dimon_2018.jpg/640px-Jamie_Dimon_2018.jpg',
            'sort_order': 4,
        },
    ]
    for preset in defaults:
        Preset.objects.get_or_create(
            label=preset['label'],
            defaults=preset,
        )


def remove_presets(apps, schema_editor):
    Preset = apps.get_model('blocks', 'CompatibilityQuickPreset')
    Preset.objects.filter(label__in=['마이클 세일러', '도널드 트럼프', '래리 핑크', '제이미 다이먼']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0043_alter_compatibilityagentprompt_model_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompatibilityQuickPreset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('birthdate', models.DateField()),
                ('birth_time', models.TimeField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, default='', max_length=10)),
                ('image_url', models.URLField(blank=True, default='')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='compatibilityquickpreset',
            index=models.Index(fields=['is_active', 'sort_order'], name='blocks_com_is_acti_f9de5b_idx'),
        ),
        migrations.RunPython(seed_presets, remove_presets),
    ]
