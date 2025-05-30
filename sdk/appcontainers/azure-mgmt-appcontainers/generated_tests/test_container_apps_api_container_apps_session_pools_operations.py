# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
import pytest
from azure.mgmt.appcontainers import ContainerAppsAPIClient

from devtools_testutils import AzureMgmtRecordedTestCase, RandomNameResourceGroupPreparer, recorded_by_proxy

AZURE_LOCATION = "eastus"


@pytest.mark.skip("you may need to update the auto-generated test case before run it")
class TestContainerAppsAPIContainerAppsSessionPoolsOperations(AzureMgmtRecordedTestCase):
    def setup_method(self, method):
        self.client = self.create_mgmt_client(ContainerAppsAPIClient)

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_list_by_subscription(self, resource_group):
        response = self.client.container_apps_session_pools.list_by_subscription(
            api_version="2025-01-01",
        )
        result = [r for r in response]
        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_list_by_resource_group(self, resource_group):
        response = self.client.container_apps_session_pools.list_by_resource_group(
            resource_group_name=resource_group.name,
            api_version="2025-01-01",
        )
        result = [r for r in response]
        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_get(self, resource_group):
        response = self.client.container_apps_session_pools.get(
            resource_group_name=resource_group.name,
            session_pool_name="str",
            api_version="2025-01-01",
        )

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_begin_create_or_update(self, resource_group):
        response = self.client.container_apps_session_pools.begin_create_or_update(
            resource_group_name=resource_group.name,
            session_pool_name="str",
            session_pool_envelope={
                "location": "str",
                "containerType": "str",
                "customContainerTemplate": {
                    "containers": [
                        {
                            "args": ["str"],
                            "command": ["str"],
                            "env": [{"name": "str", "secretRef": "str", "value": "str"}],
                            "image": "str",
                            "name": "str",
                            "resources": {"cpu": 0.0, "memory": "str"},
                        }
                    ],
                    "ingress": {"targetPort": 0},
                    "registryCredentials": {
                        "identity": "str",
                        "passwordSecretRef": "str",
                        "server": "str",
                        "username": "str",
                    },
                },
                "dynamicPoolConfiguration": {
                    "lifecycleConfiguration": {
                        "cooldownPeriodInSeconds": 0,
                        "lifecycleType": "str",
                        "maxAlivePeriodInSeconds": 0,
                    }
                },
                "environmentId": "str",
                "id": "str",
                "identity": {
                    "type": "str",
                    "principalId": "str",
                    "tenantId": "str",
                    "userAssignedIdentities": {"str": {"clientId": "str", "principalId": "str"}},
                },
                "managedIdentitySettings": [{"identity": "str", "lifecycle": "str"}],
                "name": "str",
                "nodeCount": 0,
                "poolManagementEndpoint": "str",
                "poolManagementType": "str",
                "provisioningState": "str",
                "scaleConfiguration": {"maxConcurrentSessions": 0, "readySessionInstances": 0},
                "secrets": [{"name": "str", "value": "str"}],
                "sessionNetworkConfiguration": {"status": "str"},
                "systemData": {
                    "createdAt": "2020-02-20 00:00:00",
                    "createdBy": "str",
                    "createdByType": "str",
                    "lastModifiedAt": "2020-02-20 00:00:00",
                    "lastModifiedBy": "str",
                    "lastModifiedByType": "str",
                },
                "tags": {"str": "str"},
                "type": "str",
            },
            api_version="2025-01-01",
        ).result()  # call '.result()' to poll until service return final result

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_begin_update(self, resource_group):
        response = self.client.container_apps_session_pools.begin_update(
            resource_group_name=resource_group.name,
            session_pool_name="str",
            session_pool_envelope={
                "customContainerTemplate": {
                    "containers": [
                        {
                            "args": ["str"],
                            "command": ["str"],
                            "env": [{"name": "str", "secretRef": "str", "value": "str"}],
                            "image": "str",
                            "name": "str",
                            "resources": {"cpu": 0.0, "memory": "str"},
                        }
                    ],
                    "ingress": {"targetPort": 0},
                    "registryCredentials": {
                        "identity": "str",
                        "passwordSecretRef": "str",
                        "server": "str",
                        "username": "str",
                    },
                },
                "dynamicPoolConfiguration": {
                    "lifecycleConfiguration": {
                        "cooldownPeriodInSeconds": 0,
                        "lifecycleType": "str",
                        "maxAlivePeriodInSeconds": 0,
                    }
                },
                "identity": {
                    "type": "str",
                    "principalId": "str",
                    "tenantId": "str",
                    "userAssignedIdentities": {"str": {"clientId": "str", "principalId": "str"}},
                },
                "scaleConfiguration": {"maxConcurrentSessions": 0, "readySessionInstances": 0},
                "secrets": [{"name": "str", "value": "str"}],
                "sessionNetworkConfiguration": {"status": "str"},
                "tags": {"str": "str"},
            },
            api_version="2025-01-01",
        ).result()  # call '.result()' to poll until service return final result

        # please add some check logic here by yourself
        # ...

    @RandomNameResourceGroupPreparer(location=AZURE_LOCATION)
    @recorded_by_proxy
    def test_container_apps_session_pools_begin_delete(self, resource_group):
        response = self.client.container_apps_session_pools.begin_delete(
            resource_group_name=resource_group.name,
            session_pool_name="str",
            api_version="2025-01-01",
        ).result()  # call '.result()' to poll until service return final result

        # please add some check logic here by yourself
        # ...
