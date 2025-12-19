from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0061_add_description_back_to_compatibilityquickpreset'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompatibilityReportTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('label', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('content', models.TextField()),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
