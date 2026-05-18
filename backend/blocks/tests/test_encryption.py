from django.test import SimpleTestCase

from blocks.encryption import MnemonicEncryption, encrypt_mnemonic, decrypt_mnemonic, is_encrypted_mnemonic


class MnemonicEncryptionTests(SimpleTestCase):
    def setUp(self):
        self.enc = MnemonicEncryption()
        self.sample = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'

    def test_encrypt_returns_string(self):
        token = self.enc.encrypt(self.sample)
        self.assertIsInstance(token, str)
        self.assertNotEqual(token, self.sample)

    def test_decrypt_roundtrip(self):
        token = self.enc.encrypt(self.sample)
        recovered = self.enc.decrypt(token)
        self.assertEqual(recovered, self.sample)

    def test_encrypt_different_each_call(self):
        t1 = self.enc.encrypt(self.sample)
        t2 = self.enc.encrypt(self.sample)
        self.assertNotEqual(t1, t2)

    def test_decrypt_wrong_token_raises(self):
        with self.assertRaises(Exception):
            self.enc.decrypt('this-is-not-a-valid-token')

    def test_encrypt_empty_raises(self):
        with self.assertRaises((ValueError, Exception)):
            self.enc.encrypt('')

    def test_decrypt_empty_raises(self):
        with self.assertRaises((ValueError, Exception)):
            self.enc.decrypt('')

    def test_encrypt_unicode_mnemonic(self):
        korean = '버리다 버리다 버리다 버리다 버리다 버리다 버리다 버리다 버리다 버리다 버리다 버리다'
        token = self.enc.encrypt(korean)
        self.assertEqual(self.enc.decrypt(token), korean)

    def test_module_level_encrypt_decrypt(self):
        token = encrypt_mnemonic(self.sample)
        recovered = decrypt_mnemonic(token)
        self.assertEqual(recovered, self.sample)


class IsEncryptedTests(SimpleTestCase):
    def setUp(self):
        self.enc = MnemonicEncryption()
        self.sample = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'

    def test_empty_string_returns_false(self):
        self.assertFalse(self.enc.is_encrypted(''))

    def test_none_like_short_string_returns_false(self):
        self.assertFalse(self.enc.is_encrypted('abc'))

    def test_plaintext_mnemonic_returns_false(self):
        self.assertFalse(self.enc.is_encrypted(self.sample))

    def test_real_encrypted_token_returns_true(self):
        token = self.enc.encrypt(self.sample)
        self.assertTrue(self.enc.is_encrypted(token))

    def test_random_short_base64_returns_false(self):
        self.assertFalse(self.enc.is_encrypted('aGVsbG8='))

    def test_invalid_bytes_returns_false(self):
        self.assertFalse(self.enc.is_encrypted('!@#$%^&*()')  )

    def test_convenience_function_delegates(self):
        token = encrypt_mnemonic(self.sample)
        self.assertTrue(is_encrypted_mnemonic(token))
        self.assertFalse(is_encrypted_mnemonic(self.sample))
