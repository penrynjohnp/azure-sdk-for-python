# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import pytest
from azure.keyvault.keys.crypto.aio import CryptographyClient
from devtools_testutils import set_bodiless_matcher
from devtools_testutils.aio import recorded_by_proxy_async

from _async_test_case import AsyncKeysClientPreparer, get_decorator
from _shared.test_case_async import KeyVaultTestCase

all_api_versions = get_decorator(is_async=True, only_vault=True)


class TestCryptoExamples(KeyVaultTestCase):
    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version,is_hsm",all_api_versions)
    @AsyncKeysClientPreparer()
    @recorded_by_proxy_async
    async def test_encrypt_decrypt_async(self, key_client, **kwargs):
        credential = self.get_credential(CryptographyClient, is_async=True)
        key_name = self.get_resource_name("crypto-test-encrypt-key")
        await key_client.create_rsa_key(key_name)

        # [START create_client]
        # create a CryptographyClient using a KeyVaultKey instance
        key = await key_client.get_key(key_name)
        crypto_client = CryptographyClient(key, credential)

        # or a key's id, which must include a version
        key_id = "https://<your vault>.vault.azure.net/keys/<key name>/fe4fdcab688c479a9aa80f01ffeac26"
        crypto_client = CryptographyClient(key_id, credential)

        # the client and credential should be closed when no longer needed
        # (both are also async context managers)
        await crypto_client.close()
        await credential.close()
        # [END create_client]

        client = CryptographyClient(key, credential, api_version=key_client.api_version)

        # [START encrypt]
        from azure.keyvault.keys.crypto import EncryptionAlgorithm

        # the result holds the ciphertext and identifies the encryption key and algorithm used
        result = await client.encrypt(EncryptionAlgorithm.rsa_oaep_256, b"plaintext")
        print(result.key_id)
        print(result.algorithm)
        ciphertext = result.ciphertext
        # [END encrypt]

        # [START decrypt]
        from azure.keyvault.keys.crypto import EncryptionAlgorithm

        result = await client.decrypt(EncryptionAlgorithm.rsa_oaep_256, ciphertext)
        print(result.plaintext)
        # [END decrypt]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version,is_hsm",all_api_versions)
    @AsyncKeysClientPreparer()
    @recorded_by_proxy_async
    async def test_wrap_unwrap_async(self, key_client, **kwargs):
        credential = self.get_credential(CryptographyClient, is_async=True)
        key_name = self.get_resource_name("crypto-test-wrapping-key")
        key = await key_client.create_rsa_key(key_name)
        client = CryptographyClient(key, credential, api_version=key_client.api_version)

        key_bytes = b'\xc5\xb0\xfc\xf1C\x8a\x88pj\x11\x8d\xe5\x94\xe8\xff\x04\x0eY\xfeu\x8a\xe9<\x06(\xdb\x7f\xa9~\x85\x02\x04'

        # [START wrap_key]
        from azure.keyvault.keys.crypto import KeyWrapAlgorithm

        # wrap returns a tuple with the wrapped bytes and the metadata required to unwrap the key
        result = await client.wrap_key(KeyWrapAlgorithm.rsa_oaep_256, key_bytes)
        print(result.key_id)
        print(result.algorithm)
        encrypted_key = result.encrypted_key
        # [END wrap_key]

        # [START unwrap_key]
        from azure.keyvault.keys.crypto import KeyWrapAlgorithm

        result = await client.unwrap_key(KeyWrapAlgorithm.rsa_oaep_256, encrypted_key)
        # [END unwrap_key]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version,is_hsm",all_api_versions)
    @AsyncKeysClientPreparer()
    @recorded_by_proxy_async
    async def test_sign_verify_async(self, key_client, **kwargs):
        credential = self.get_credential(CryptographyClient, is_async=True)
        key_name = self.get_resource_name("crypto-test-wrapping-key")
        key = await key_client.create_rsa_key(key_name)
        client = CryptographyClient(key, credential, api_version=key_client.api_version)

        # [START sign]
        import hashlib

        from azure.keyvault.keys.crypto import SignatureAlgorithm

        digest = hashlib.sha256(b"plaintext").digest()

        # sign returns the signature and the metadata required to verify it
        result = await client.sign(SignatureAlgorithm.rs256, digest)
        print(result.key_id)
        print(result.algorithm)
        signature = result.signature
        # [END sign]

        # [START verify]
        from azure.keyvault.keys.crypto import SignatureAlgorithm

        verified = await client.verify(SignatureAlgorithm.rs256, digest, signature)
        assert verified.is_valid
        # [END verify]
