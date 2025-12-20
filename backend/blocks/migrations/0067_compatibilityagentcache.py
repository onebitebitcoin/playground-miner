from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0066_update_report_templates_tone'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompatibilityAgentCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_key', models.CharField(max_length=100)),
                ('category', models.CharField(blank=True, default='', max_length=100)),
                ('cache_key', models.CharField(max_length=128, unique=True)),
                ('subject_name', models.CharField(blank=True, default='', max_length=120)),
                ('target_name', models.CharField(blank=True, default='', max_length=120)),
                ('profile_signature', models.CharField(blank=True, default='', max_length=255)),
                ('target_signature', models.CharField(blank=True, default='', max_length=255)),
                ('request_payload', models.JSONField(blank=True, default=dict)),
                ('response_text', models.TextField(blank=True, default='')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('hit_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='compatibilityagentcache',
            index=models.Index(fields=['category'], name='blocks_comp_category_0c2b59_idx'),
        ),
        migrations.AddIndex(
            model_name='compatibilityagentcache',
            index=models.Index(fields=['subject_name'], name='blocks_comp_subject_172a70_idx'),
        ),
        migrations.AddIndex(
            model_name='compatibilityagentcache',
            index=models.Index(fields=['target_name'], name='blocks_comp_target__a9e5a2_idx'),
        ),
        migrations.AddIndex(
            model_name='compatibilityagentcache',
            index=models.Index(fields=['updated_at'], name='blocks_comp_updated_6e8ba1_idx'),
        ),
    ]

