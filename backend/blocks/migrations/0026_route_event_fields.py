from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0025_servicenode_node_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='is_event',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='route',
            name='event_title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='route',
            name='event_description',
            field=models.TextField(blank=True, default=''),
        ),
    ]

