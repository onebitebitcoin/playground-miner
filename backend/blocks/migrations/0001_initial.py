from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('height', models.PositiveIntegerField(unique=True)),
                ('nonce', models.PositiveIntegerField()),
                ('miner', models.CharField(max_length=64)),
                ('difficulty', models.PositiveIntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-height']},
        ),
    ]

