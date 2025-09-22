from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0012_servicenode_route'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoutingSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('nodes_json', models.JSONField()),
                ('routes_json', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]

