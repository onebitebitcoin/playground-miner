from django.db import migrations


def cleanup_templates(apps, schema_editor):
    Template = apps.get_model('blocks', 'CompatibilityReportTemplate')
    Template.objects.filter(key='target_vs_bitcoin').delete()
    Template.objects.filter(key='user_vs_bitcoin').update(label='개별 사용자와 비트코인의 궁합')
    Template.objects.filter(key='team_vs_bitcoin').update(label='두 사용자의 비트코인 궁합')


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0064_set_gpt5_for_compat_agents'),
    ]

    operations = [
        migrations.RunPython(cleanup_templates, migrations.RunPython.noop),
    ]
