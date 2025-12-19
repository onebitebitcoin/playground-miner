from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0069_store_plain_mnemonics'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeCapsuleBroadcastSetting',
            fields=[
                ('id', models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ('fullnode_host', models.CharField(blank=True, default='', max_length=255)),
                ('fullnode_port', models.PositiveIntegerField(default=8332)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
