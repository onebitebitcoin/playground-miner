from django.db import migrations, models


def _set_openai_default(apps, schema_editor):
    Prompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    for prompt in Prompt.objects.all():
        prompt.model_name = 'gpt-4o-mini'
        prompt.save(update_fields=['model_name', 'updated_at'])


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0042_alter_compatibilityagentprompt_model_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compatibilityagentprompt',
            name='model_name',
            field=models.CharField(default='gpt-4o-mini', max_length=100),
        ),
        migrations.RunPython(_set_openai_default, _noop),
    ]
