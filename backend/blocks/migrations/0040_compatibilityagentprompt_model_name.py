from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0039_compatibilityanalysis_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='compatibilityagentprompt',
            name='model_name',
            field=models.CharField(default='gpt-5.0', max_length=100),
        ),
    ]
