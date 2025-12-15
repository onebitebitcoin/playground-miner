from django.db import migrations
from blocks.prompts import COMPATIBILITY_AGENT_DEFAULT_PROMPT

def update_prompt_content(apps, schema_editor):
    CompatibilityAgentPrompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    # Update all prompts to the new refined version
    CompatibilityAgentPrompt.objects.all().update(system_prompt=COMPATIBILITY_AGENT_DEFAULT_PROMPT)

class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0052_update_existing_compatibility_models'),
    ]

    operations = [
        migrations.RunPython(update_prompt_content),
    ]