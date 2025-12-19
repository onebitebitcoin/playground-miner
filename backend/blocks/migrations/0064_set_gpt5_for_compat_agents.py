from django.db import migrations


def set_gpt5_model(apps, schema_editor):
    Prompt = apps.get_model('blocks', 'CompatibilityAgentPrompt')
    Prompt.objects.all().update(model_name='openai:gpt-5-mini')


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0063_update_report_templates'),
    ]

    operations = [
        migrations.RunPython(set_gpt5_model, migrations.RunPython.noop),
    ]
