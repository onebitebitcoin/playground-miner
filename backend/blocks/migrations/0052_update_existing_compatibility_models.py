from django.db import migrations

def update_compatibility_models(apps, schema_editor):
    CompatibilityAgentPrompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    # Update all to the new default
    CompatibilityAgentPrompt.objects.all().update(model_name='openai:gpt-5-mini')

class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0051_alter_compatibilityagentprompt_model_name'),
    ]

    operations = [
        migrations.RunPython(update_compatibility_models),
    ]