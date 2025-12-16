from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0040_compatibilityagentprompt_model_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compatibilityagentprompt',
            name='model_name',
            field=models.CharField(default='gemini-1.5-pro', max_length=100),
        ),
    ]
