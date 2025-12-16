from django.db import migrations, models


def create_default_prompt(apps, schema_editor):
    CompatibilityAgentPrompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    try:
        from blocks.prompts import COMPATIBILITY_AGENT_DEFAULT_PROMPT
    except Exception:
        COMPATIBILITY_AGENT_DEFAULT_PROMPT = ''

    CompatibilityAgentPrompt.objects.get_or_create(
        agent_key='saju_bitcoin',
        defaults={
            'name': '비트코인 궁합 에이전트',
            'description': '비트코인을 디지털 금으로 정의하는 사주 분석 전문가 프롬프트',
            'system_prompt': COMPATIBILITY_AGENT_DEFAULT_PROMPT or '비트코인 궁합 에이전트 기본 프롬프트',
            'is_active': True,
        }
    )


def delete_default_prompt(apps, schema_editor):
    CompatibilityAgentPrompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    CompatibilityAgentPrompt.objects.filter(agent_key='saju_bitcoin').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0037_rename_blocks_asse_asset_i_b8e9f5_idx_blocks_asse_asset_i_6897e7_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompatibilityAgentPrompt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_key', models.CharField(db_index=True, max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('system_prompt', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['agent_key'],
            },
        ),
        migrations.AddIndex(
            model_name='compatibilityagentprompt',
            index=models.Index(fields=['agent_key'], name='blocks_comp_agent_k_17717e_idx'),
        ),
        migrations.AddIndex(
            model_name='compatibilityagentprompt',
            index=models.Index(fields=['is_active'], name='blocks_comp_is_acti_8224ad_idx'),
        ),
        migrations.RunPython(create_default_prompt, delete_default_prompt),
    ]
