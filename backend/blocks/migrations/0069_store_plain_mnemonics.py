from django.db import migrations


def store_plain_mnemonics(apps, schema_editor):
    Mnemonic = apps.get_model('blocks', 'Mnemonic')

    try:
        from blocks.encryption import decrypt_mnemonic, is_encrypted_mnemonic
    except Exception:
        decrypt_mnemonic = None
        is_encrypted_mnemonic = None

    for mnemonic in Mnemonic.objects.all():
        value = mnemonic.mnemonic or ''
        if not value:
            continue

        # Attempt to decrypt existing values if possible.
        if decrypt_mnemonic and is_encrypted_mnemonic and is_encrypted_mnemonic(value):
            try:
                plaintext = decrypt_mnemonic(value)
            except Exception:
                # Unable to decrypt; leave value as-is so admins can recreate if needed.
                continue
            else:
                Mnemonic.objects.filter(pk=mnemonic.pk).update(mnemonic=plaintext)


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0068_timecapsule_clear_addresses'),
    ]

    operations = [
        migrations.RunPython(store_plain_mnemonics, migrations.RunPython.noop),
    ]
