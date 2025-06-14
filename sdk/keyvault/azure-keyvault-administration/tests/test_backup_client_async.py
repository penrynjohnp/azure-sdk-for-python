# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import asyncio

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.keyvault.administration._internal.client_base import DEFAULT_VERSION
from devtools_testutils import set_bodiless_matcher
from devtools_testutils.aio import recorded_by_proxy_async

from _async_test_case import KeyVaultBackupClientPreparer, KeyVaultBackupClientSasPreparer, get_decorator
from _shared.test_case_async import KeyVaultTestCase

all_api_versions = get_decorator(is_async=True)
only_default = get_decorator(is_async=True, api_versions=[DEFAULT_VERSION])


class TestBackupClientTests(KeyVaultTestCase):
    def create_key_client(self, vault_uri, **kwargs):
         from azure.keyvault.keys.aio import KeyClient
         credential = self.get_credential(KeyClient, is_async=True)
         return self.create_client_from_credential(KeyClient, credential=credential, vault_url=vault_uri, **kwargs )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", only_default)
    @KeyVaultBackupClientPreparer()
    @recorded_by_proxy_async
    async def test_full_backup_and_restore(self, client, **kwargs):
        set_bodiless_matcher()
        # backup the vault
        container_uri = kwargs.pop("container_uri")
        # make sure an error isn't raised by pre-backup check; i.e. ensure the backup can be done
        check_poller = await client.begin_pre_backup(container_uri, use_managed_identity=True)
        await check_poller.wait()
        backup_poller = await client.begin_backup(container_uri, use_managed_identity=True)
        backup_operation = await backup_poller.result()
        assert backup_operation.folder_url

        if self.is_live:
            await asyncio.sleep(15)  # Additional waiting to ensure backup will be available for restore

        # restore the backup
        # make sure an error isn't raised by pre-restore check; i.e. ensure the restore can be done
        check_poller = await client.begin_pre_restore(backup_operation.folder_url, use_managed_identity=True)
        await check_poller.wait()
        restore_poller = await client.begin_restore(backup_operation.folder_url, use_managed_identity=True)
        await restore_poller.wait()
        if self.is_live:
            await asyncio.sleep(60)  # additional waiting to avoid conflicts with resources in other tests

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", only_default)
    @KeyVaultBackupClientPreparer()
    @recorded_by_proxy_async
    async def test_full_backup_and_restore_rehydration(self, client, **kwargs):
        set_bodiless_matcher()

        # backup the vault
        container_uri = kwargs.pop("container_uri")
        backup_poller = await client.begin_backup(blob_storage_url=container_uri, use_managed_identity=True)

        # create a new poller from a continuation token
        token = backup_poller.continuation_token()
        rehydrated = await client.begin_backup(container_uri, use_managed_identity=True, continuation_token=token)

        if self.is_live:
            await asyncio.sleep(15)  # Additional waiting to ensure backup will be available for restore

        rehydrated_operation = await rehydrated.result()
        assert rehydrated_operation.folder_url
        backup_operation = await backup_poller.result()
        assert backup_operation.folder_url == rehydrated_operation.folder_url

        # restore the backup
        restore_poller = await client.begin_restore(backup_operation.folder_url, use_managed_identity=True)

        # create a new poller from a continuation token
        token = restore_poller.continuation_token()
        rehydrated = await client.begin_restore(
            backup_operation.folder_url, use_managed_identity=True, continuation_token=token
        )

        await rehydrated.wait()
        await restore_poller.wait()
        if self.is_live:
            await asyncio.sleep(60)  # additional waiting to avoid conflicts with resources in other tests

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", only_default)
    @KeyVaultBackupClientPreparer()
    @recorded_by_proxy_async
    async def test_selective_key_restore(self, client, **kwargs):
        set_bodiless_matcher()
        # create a key to selectively restore
        managed_hsm_url = kwargs.pop("managed_hsm_url")
        key_client = self.create_key_client(managed_hsm_url, is_async=True)
        key_name = self.get_resource_name("selective-restore-test-key")
        await key_client.create_rsa_key(key_name)

        # backup the vault
        container_uri = kwargs.pop("container_uri")
        backup_poller = await client.begin_backup(container_uri, use_managed_identity=True)
        backup_operation = await backup_poller.result()

        if self.is_live:
            await asyncio.sleep(15)  # Additional waiting to ensure backup will be available for restore

        # restore the key
        restore_poller = await client.begin_restore(
            backup_operation.folder_url, use_managed_identity=True, key_name=key_name
        )
        await restore_poller.wait()

        # delete the key
        await self._poll_until_no_exception(key_client.delete_key, key_name, expected_exception=ResourceExistsError)
        await key_client.purge_deleted_key(key_name)
        if self.is_live:
            await asyncio.sleep(60)  # additional waiting to avoid conflicts with resources in other tests

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", only_default)
    @KeyVaultBackupClientPreparer()
    @recorded_by_proxy_async
    async def test_backup_client_polling(self, client, **kwargs):
        set_bodiless_matcher()

        # backup the vault
        container_uri = kwargs.pop("container_uri")
        backup_poller = await client.begin_backup(container_uri, use_managed_identity=True)

        # create a new poller from a continuation token
        token = backup_poller.continuation_token()
        rehydrated = await client.begin_backup(container_uri, use_managed_identity=True, continuation_token=token)

        # check that pollers and polling methods behave as expected
        if self.is_live:
            assert backup_poller.status() == "InProgress"
        assert not backup_poller.done() or backup_poller.polling_method().finished()
        #assert rehydrated.status() == "InProgress"
        assert not rehydrated.done() or rehydrated.polling_method().finished()

        backup_operation = await backup_poller.result()
        assert backup_poller.status() == "Succeeded" and backup_poller.polling_method().status() == "Succeeded"
        rehydrated_operation = await rehydrated.result()
        assert rehydrated.status() == "Succeeded" and rehydrated.polling_method().status() == "Succeeded"
        assert backup_operation.folder_url == rehydrated_operation.folder_url

        # rehydrate a poller with a continuation token of a completed operation
        late_rehydrated = await client.begin_backup(container_uri, use_managed_identity=True, continuation_token=token)
        assert late_rehydrated.status() == "Succeeded"
        await late_rehydrated.wait()

        if self.is_live:
            await asyncio.sleep(15)  # Additional waiting to ensure backup will be available for restore

        # restore the backup
        restore_poller = await client.begin_restore(backup_operation.folder_url, use_managed_identity=True)

        # create a new poller from a continuation token
        token = restore_poller.continuation_token()
        rehydrated = await client.begin_restore(
            backup_operation.folder_url, use_managed_identity=True, continuation_token=token
        )

        # check that pollers and polling methods behave as expected
        if self.is_live:
            assert restore_poller.status() == "InProgress"
        assert not restore_poller.done() or restore_poller.polling_method().finished()
        #assert rehydrated.status() == "InProgress"
        assert not rehydrated.done() or rehydrated.polling_method().finished()

        await rehydrated.wait()
        assert rehydrated.status() == "Succeeded" and rehydrated.polling_method().status() == "Succeeded"
        await restore_poller.wait()
        assert restore_poller.status() == "Succeeded" and restore_poller.polling_method().status() == "Succeeded"

        if self.is_live:
            await asyncio.sleep(60)  # additional waiting to avoid conflicts with resources in other tests

    @pytest.mark.live_test_only
    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", only_default)
    @KeyVaultBackupClientSasPreparer()
    async def test_backup_restore_sas(self, client, **kwargs):
        # backup the vault
        container_uri = kwargs.pop("container_uri")
        sas_token = kwargs.pop("sas_token")

        if self.is_live and not sas_token:
            pytest.skip("SAS token is required for live tests. Please set the BLOB_STORAGE_SAS_TOKEN environment variable.")

        check_poller = await client.begin_pre_backup(container_uri, sas_token=sas_token)
        await check_poller.wait()
        backup_poller = await client.begin_backup(container_uri, sas_token)
        backup_operation = await backup_poller.result()
        assert backup_operation.folder_url

        if self.is_live:
            await asyncio.sleep(15)  # Additional waiting to ensure backup will be available for restore

        # restore the backup
        check_poller = await client.begin_pre_restore(backup_operation.folder_url, sas_token=sas_token)
        check_result = await check_poller.result()
        assert check_result.error is None
        restore_poller = await client.begin_restore(backup_operation.folder_url, sas_token)
        await restore_poller.wait()
        if self.is_live:
            await asyncio.sleep(60)  # additional waiting to avoid conflicts with resources in other tests
