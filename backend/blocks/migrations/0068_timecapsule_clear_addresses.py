from django.db import migrations


def clear_time_capsule_addresses(apps, schema_editor):
    TimeCapsule = apps.get_model('blocks', 'TimeCapsule')
    TimeCapsule.objects.exclude(bitcoin_address='').update(
        bitcoin_address='',
        mnemonic=None,
        address_index=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0067_mnemonic_next_address_index_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_time_capsule_addresses, migrations.RunPython.noop),
    ]
