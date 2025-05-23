# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import os
import time

from azure.keyvault.certificates import CertificateClient, CertificatePolicy
from azure.identity import DefaultAzureCredential

# ----------------------------------------------------------------------------------------------------------
# Prerequisites:
# 1. An Azure Key Vault (https://learn.microsoft.com/azure/key-vault/quick-create-cli)
#
# 2. azure-keyvault-certificates and azure-identity packages (pip install these)
#
# 3. Set up your environment to use azure-identity's DefaultAzureCredential. For more information about how to configure
#    the DefaultAzureCredential, refer to https://aka.ms/azsdk/python/identity/docs#azure.identity.DefaultAzureCredential
#
# ----------------------------------------------------------------------------------------------------------
# Sample - demonstrates the basic backup and restore operations on a vault(certificates) resource for Azure Key Vault
#
# 1. Create a certificate (begin_create_certificate)
#
# 2. Backup a certificate (backup_certificate)
#
# 3. Delete a certificate (begin_delete_certificate)
#
# 4. Purge a certificate (purge_deleted_certificate)
#
# 5. Restore a certificate (restore_certificate_backup)
# ----------------------------------------------------------------------------------------------------------

# Instantiate a certificate client that will be used to call the service.
# Here we use the DefaultAzureCredential, but any azure-identity credential can be used.
VAULT_URL = os.environ["VAULT_URL"]
credential = DefaultAzureCredential()
client = CertificateClient(vault_url=VAULT_URL, credential=credential)

print("\n.. Create Certificate")
cert_name = "BackupRestoreCertificate"

# Let's create a certificate for your key vault.
# if the certificate already exists in the Key Vault, then a new version of the certificate is created.
# A long running poller is returned for the create certificate operation.
create_certificate_poller = client.begin_create_certificate(
    certificate_name=cert_name, policy=CertificatePolicy.get_default()
)

# The result call awaits the completion of the create certificate operation and returns the final result.
# It will return a certificate if creation is successful, and will return the CertificateOperation if not.
certificate = create_certificate_poller.result()
print(f"Certificate with name '{cert_name}' created.")

# Backups are good to have, if in case certificates gets deleted accidentally.
# For long term storage, it is ideal to write the backup to a file.
print("\n.. Create a backup for an existing certificate")
certificate_backup = client.backup_certificate(cert_name)
print(f"Backup created for certificate with name '{cert_name}'.")

# The storage account certificate is no longer in use, so you can delete it.
print("\n.. Delete the certificate")
delete_operation = client.begin_delete_certificate(cert_name)
deleted_certificate = delete_operation.result()
assert deleted_certificate.name
print(f"Deleted certificate with name '{deleted_certificate.name}'")

# Wait for the deletion to complete before purging the certificate.
# The purge will take some time, so wait before restoring the backup to avoid a conflict.
delete_operation.wait()
print("\n.. Purge the certificate")
client.purge_deleted_certificate(deleted_certificate.name)
time.sleep(60)
print(f"Purged certificate with name '{deleted_certificate.name}'")

# In the future, if the certificate is required again, we can use the backup value to restore it in the Key Vault.
print("\n.. Restore the certificate from the backup")
certificate = client.restore_certificate_backup(certificate_backup)
print(f"Restored certificate with name '{certificate.name}'")

print("\nrun_sample done")
