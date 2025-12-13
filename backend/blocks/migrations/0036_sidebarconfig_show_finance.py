from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0035_assetpricecache'),
    ]

    operations = [
        migrations.AddField(
            model_name='sidebarconfig',
            name='show_finance',
            field=models.BooleanField(default=False),
        ),
    ]
