from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0002_add_reward'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nickname',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

