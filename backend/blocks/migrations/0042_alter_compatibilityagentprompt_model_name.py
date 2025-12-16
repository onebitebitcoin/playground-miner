from django.db import migrations, models


def _set_default_model(apps, schema_editor):
    Prompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    for prompt in Prompt.objects.all():
        current = (prompt.model_name or '').strip().lower()
        if not current or current.startswith('gpt-'):
            prompt.model_name = 'gemini-2.5-pro'
            prompt.save(update_fields=['model_name', 'updated_at'])


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0041_alter_compatibilityagentprompt_model_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compatibilityagentprompt',
            name='model_name',
            field=models.CharField(default='gemini-2.5-pro', max_length=100),
        ),
        migrations.RunPython(_set_default_model, _noop),
    ]
