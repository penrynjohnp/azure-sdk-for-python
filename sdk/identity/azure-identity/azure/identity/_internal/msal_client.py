# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import threading
from typing import Any, Dict, Optional, Union

from azure.core.exceptions import ClientAuthenticationError
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.core.pipeline.transport import (  # pylint:disable=no-legacy-azure-core-http-response-import
    HttpRequest,
    HttpResponse,
)
from azure.core.pipeline import PipelineResponse
from .pipeline import build_pipeline

RequestData = Union[Dict[str, str], str]
_POST = ["POST"]


class MsalResponse:
    """Wraps HttpResponse according to msal.oauth2cli.http.

    :param response: The response to wrap.
    :type response: ~azure.core.pipeline.transport.HttpResponse
    """

    def __init__(self, response: PipelineResponse) -> None:
        self._response = response
        self.headers = response.http_response.headers if response.http_response else {}

    @property
    def status_code(self) -> int:
        return self._response.http_response.status_code

    @property
    def text(self) -> str:
        return self._response.http_response.text(encoding="utf-8")

    def raise_for_status(self):
        if self.status_code < 400:
            return

        if ContentDecodePolicy.CONTEXT_NAME in self._response.context:
            content = self._response.context[ContentDecodePolicy.CONTEXT_NAME]
            if not content:
                message = "Unexpected response from Microsoft Entra ID"
            elif "error" in content or "error_description" in content:
                message = "Authentication failed: {}".format(content.get("error_description") or content.get("error"))
            else:
                for secret in ("access_token", "refresh_token"):
                    if secret in content:
                        content[secret] = "***"
                message = 'Unexpected response from Microsoft Entra ID: "{}"'.format(content)
        else:
            message = "Unexpected response from Microsoft Entra ID"

        raise ClientAuthenticationError(message=message, response=self._response.http_response)


class MsalClient:  # pylint:disable=client-accepts-api-version-keyword
    """Wraps Pipeline according to msal.oauth2cli.http"""

    def __init__(self, **kwargs: Any) -> None:  # pylint:disable=missing-client-constructor-parameter-credential
        self._local = threading.local()
        self._pipeline = build_pipeline(**kwargs)

    def __enter__(self) -> "MsalClient":
        self._pipeline.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        self._pipeline.__exit__(*args)

    def close(self) -> None:
        self.__exit__()

    def post(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[RequestData] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> MsalResponse:
        # pylint:disable=unused-argument
        request = HttpRequest("POST", url, headers=headers)
        if params:
            request.format_parameters(params)
        if data:
            if isinstance(data, dict):
                request.headers["Content-Type"] = "application/x-www-form-urlencoded"
                request.set_formdata_body(data)
            elif isinstance(data, str):
                body_bytes = data.encode("utf-8")
                request.set_bytes_body(body_bytes)
            else:
                raise ValueError('expected "data" to be text or a dict')

        response = self._pipeline.run(request, stream=False, retry_on_methods=_POST)
        self._store_auth_error(response)
        return MsalResponse(response)

    def get(
        self, url: str, params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> MsalResponse:
        # pylint:disable=unused-argument
        request = HttpRequest("GET", url, headers=headers)
        if params:
            request.format_parameters(params)
        response = self._pipeline.run(request, stream=False)
        self._store_auth_error(response)
        return MsalResponse(response)

    def get_error_response(self, msal_result: Dict) -> Optional[HttpResponse]:
        """Get the HTTP response associated with an MSAL error.

        :param msal_result: The result of an MSAL request.
        :type msal_result: dict
        :return: The HTTP response associated with the error, if any.
        :rtype: ~azure.core.pipeline.transport.HttpResponse or None
        """
        error_code, response = getattr(self._local, "error", (None, None))
        if response and error_code == msal_result.get("error"):
            return response
        return None

    def _store_auth_error(self, response: PipelineResponse) -> None:
        if response.http_response.status_code >= 400:
            # if the body doesn't contain "error", this isn't an OAuth 2 error, i.e. this isn't a
            # response to an auth request, so no credential will want to include it with an exception
            content = response.context.get(ContentDecodePolicy.CONTEXT_NAME)
            if content and "error" in content:
                error_code = content["error"] if isinstance(content, dict) else "oauth_error"
                self._local.error = (error_code, response.http_response)

    def __getstate__(self) -> Dict[str, Any]:  # pylint:disable=client-method-name-no-double-underscore
        state = self.__dict__.copy()
        # Remove the non-picklable entries
        del state["_local"]
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:  # pylint:disable=client-method-name-no-double-underscore
        self.__dict__.update(state)
        # Re-create the unpickable entries
        self._local = threading.local()
