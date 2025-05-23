# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
from itertools import product
import pytest

from azure.identity import (
    DefaultAzureCredential,
    CertificateCredential,
    ClientSecretCredential,
    DeviceCodeCredential,
    UsernamePasswordCredential,
    AzureCliCredential,
    AzurePowerShellCredential,
    AzureDeveloperCliCredential,
)
from azure.identity._constants import DEVELOPER_SIGN_ON_CLIENT_ID

from helpers import get_token_payload_contents, GET_TOKEN_METHODS

GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def get_token(credential, method, **kwargs):
    token = getattr(credential, method)(GRAPH_SCOPE, **kwargs)
    assert token
    assert token.token
    assert token.expires_on
    return token


@pytest.mark.parametrize(
    "certificate_fixture,get_token_method", product(("live_pem_certificate", "live_pfx_certificate"), GET_TOKEN_METHODS)
)
def test_certificate_credential(certificate_fixture, get_token_method, request):
    cert = request.getfixturevalue(certificate_fixture)

    tenant_id = cert["tenant_id"]
    client_id = cert["client_id"]

    credential = CertificateCredential(tenant_id, client_id, cert["cert_path"])
    get_token(credential, get_token_method)

    credential = CertificateCredential(tenant_id, client_id, certificate_data=cert["cert_bytes"])
    token = get_token(credential, get_token_method, enable_cae=True)
    parsed_payload = get_token_payload_contents(token.token)
    assert "xms_cc" in parsed_payload and "CP1" in parsed_payload["xms_cc"]

    if "password" in cert:
        credential = CertificateCredential(
            tenant_id, client_id, cert["cert_with_password_path"], password=cert["password"]
        )
        get_token(credential, get_token_method)

        credential = CertificateCredential(
            tenant_id, client_id, certificate_data=cert["cert_with_password_bytes"], password=cert["password"]
        )
        get_token(credential, get_token_method)


@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_client_secret_credential(live_service_principal, get_token_method):
    credential = ClientSecretCredential(
        live_service_principal["tenant_id"],
        live_service_principal["client_id"],
        live_service_principal["client_secret"],
    )
    kwargs = {"enable_cae": True}
    if get_token_method == "get_token_info":
        kwargs = {"options": kwargs}
    token = get_token(credential, get_token_method, **kwargs)
    parsed_payload = get_token_payload_contents(token.token)
    assert "xms_cc" in parsed_payload and "CP1" in parsed_payload["xms_cc"]


@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_default_credential(live_service_principal, get_token_method):
    credential = DefaultAzureCredential()
    get_token(credential, get_token_method)


@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_username_password_auth(live_user_details, get_token_method):
    credential = UsernamePasswordCredential(
        client_id=live_user_details["client_id"],
        username=live_user_details["username"],
        password=live_user_details["password"],
        tenant_id=live_user_details["tenant"],
    )
    get_token(credential, get_token_method)


@pytest.mark.manual
@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_cli_credential(get_token_method):
    credential = AzureCliCredential()
    get_token(credential, get_token_method)


@pytest.mark.manual
@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_dev_cli_credential(get_token_method):
    credential = AzureDeveloperCliCredential()
    get_token(credential, get_token_method)


@pytest.mark.manual
@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_powershell_credential(get_token_method):
    credential = AzurePowerShellCredential()
    get_token(credential, get_token_method)


@pytest.mark.manual
@pytest.mark.prints
@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_device_code(get_token_method):
    import webbrowser

    def prompt(url, user_code, _):
        print("opening a browser to '{}', enter device code {}".format(url, user_code))
        webbrowser.open_new_tab(url)

    credential = DeviceCodeCredential(client_id=DEVELOPER_SIGN_ON_CLIENT_ID, prompt_callback=prompt, timeout=40)
    get_token(credential, get_token_method)
