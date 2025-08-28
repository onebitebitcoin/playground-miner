from django.db import migrations, models


def backfill_rewards(apps, schema_editor):
    Block = apps.get_model('blocks', 'Block')

    def calc_reward(height: int) -> int:
        step = (height - 1) // 20
        r = 100 // (2 ** step)
        return max(1, r)

    for b in Block.objects.all():
        b.reward = calc_reward(b.height)
        b.save(update_fields=['reward'])


class Migration(migrations.Migration):
    dependencies = [
        ('blocks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='reward',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_rewards, migrations.RunPython.noop),
    ]

