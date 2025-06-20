# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from typing import (
    Any, cast, Dict, Literal, Optional, Union,
    TYPE_CHECKING
)

from azure.storage.blob._serialize import _get_match_headers
from ._generated.models import (
    CpkInfo,
    LeaseAccessConditions,
    ModifiedAccessConditions,
    PathHTTPHeaders,
    SourceModifiedAccessConditions,
)
from ._shared import encode_base64

if TYPE_CHECKING:
    from datetime import datetime
    from azure.storage.blob import BlobLeaseClient
    from azure.storage.blob.aio import BlobLeaseClient as BlobLeaseClientAsync
    from azure.storage.filedatalake import CustomerProvidedEncryptionKey
    from ._models import ContentSettings

EncryptionAlgorithmType = Literal["AES256"]

_SUPPORTED_API_VERSIONS = [
    '2019-02-02',
    '2019-07-07',
    '2019-10-10',
    '2019-12-12',
    '2020-02-10',
    '2020-04-08',
    '2020-06-12',
    '2020-08-04',
    '2020-10-02',
    '2020-12-06',
    '2021-02-12',
    '2021-04-10',
    '2021-06-08',
    '2021-08-06',
    '2021-12-02',
    '2022-11-02',
    '2023-01-03',
    '2023-05-03',
    '2023-08-03',
    '2023-11-03',
    '2024-05-04',
    '2024-08-04',
    '2024-11-04',
    '2025-01-05',
    '2025-05-05',
    '2025-07-05',
    '2025-11-05',
]  # This list must be in chronological order!


def get_api_version(kwargs: Dict[str, Any]) -> str:
    api_version = kwargs.get('api_version', None)
    if api_version and api_version not in _SUPPORTED_API_VERSIONS:
        versions = '\n'.join(_SUPPORTED_API_VERSIONS)
        raise ValueError(f"Unsupported API version '{api_version}'. Please select from:\n{versions}")
    return api_version or _SUPPORTED_API_VERSIONS[-1]


def compare_api_versions(version1: str, version2: str) -> int:
    v1 = _SUPPORTED_API_VERSIONS.index(version1)
    v2 = _SUPPORTED_API_VERSIONS.index(version2)
    if v1 == v2:
        return 0
    if v1 < v2:
        return -1
    return 1


def convert_dfs_url_to_blob_url(dfs_account_url: str) -> str:
    return dfs_account_url.replace('.dfs.', '.blob.', 1)


def convert_datetime_to_rfc1123(date: "datetime") -> str:
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"][date.month - 1]
    return f"{weekday}, {date.day:02} {month} {date.year:04} {date.hour:02}:{date.minute:02}:{date.second:02} GMT"


def add_metadata_headers(metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
    if not metadata:
        return None
    headers = []
    if metadata:
        for key, value in metadata.items():
            headers.append(key + '=')
            headers.append(encode_base64(value))
            headers.append(',')

    if headers:
        del headers[-1]

    return ''.join(headers)


def get_mod_conditions(kwargs: Dict[str, Any]) -> ModifiedAccessConditions:
    if_match, if_none_match = _get_match_headers(kwargs, 'match_condition', 'etag')
    return ModifiedAccessConditions(
        if_modified_since=kwargs.pop('if_modified_since', None),
        if_unmodified_since=kwargs.pop('if_unmodified_since', None),
        if_match=if_match or kwargs.pop('if_match', None),
        if_none_match=if_none_match or kwargs.pop('if_none_match', None)
    )


def get_source_mod_conditions(kwargs: Dict[str, Any]) -> SourceModifiedAccessConditions:
    if_match, if_none_match = _get_match_headers(kwargs, 'source_match_condition', 'source_etag')
    return SourceModifiedAccessConditions(
        source_if_modified_since=kwargs.pop('source_if_modified_since', None),
        source_if_unmodified_since=kwargs.pop('source_if_unmodified_since', None),
        source_if_match=if_match or kwargs.pop('source_if_match', None),
        source_if_none_match=if_none_match or kwargs.pop('source_if_none_match', None)
    )


def get_path_http_headers(content_settings: "ContentSettings") -> PathHTTPHeaders:
    path_headers = PathHTTPHeaders(
        cache_control=content_settings.cache_control,
        content_type=content_settings.content_type,
        content_md5=bytearray(content_settings.content_md5) if content_settings.content_md5 else None,
        content_encoding=content_settings.content_encoding,
        content_language=content_settings.content_language,
        content_disposition=content_settings.content_disposition
    )
    return path_headers


def get_access_conditions(
    lease: Optional[Union["BlobLeaseClient", "BlobLeaseClientAsync", str]]
) -> Optional[LeaseAccessConditions]:
    if not lease:
        return None
    if hasattr(lease, "id"):
        lease_id = lease.id
    else:
        lease_id = lease
    return LeaseAccessConditions(lease_id=lease_id)


def get_lease_id(lease: Optional[Union["BlobLeaseClient", "BlobLeaseClientAsync", str]]) -> str:
    if not lease:
        return ""
    if hasattr(lease, "id"):
        lease_id = lease.id
    else:
        lease_id = lease
    return lease_id


def get_lease_action_properties(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    lease_action = kwargs.pop('lease_action', None)
    lease_duration = kwargs.pop('lease_duration', None)
    lease = kwargs.pop('lease', None)
    if hasattr(lease, "id"):
        lease_id = lease.id
    else:
        lease_id = lease

    proposed_lease_id = None
    access_conditions = None

    # Acquiring a new lease
    if lease_action in ['acquire', 'acquire-release']:
        # Use provided lease id as the new lease id
        proposed_lease_id = lease_id
        # Assign a default lease duration if not provided
        lease_duration = lease_duration or -1
    else:
        # Use lease id as access conditions
        access_conditions = LeaseAccessConditions(lease_id=lease_id) if lease_id else None

    return {
        'lease_action': lease_action,
        'lease_duration': lease_duration,
        'proposed_lease_id': proposed_lease_id,
        'lease_access_conditions': access_conditions
    }


def get_cpk_info(scheme: str, kwargs: Dict[str, Any]) -> Optional[CpkInfo]:
    cpk: Optional[CustomerProvidedEncryptionKey] = kwargs.pop('cpk', None)
    if cpk:
        if scheme.lower() != 'https':
            raise ValueError("Customer provided encryption key must be used over HTTPS.")
        return CpkInfo(
            encryption_key=cpk.key_value,
            encryption_key_sha256=cpk.key_hash,
            encryption_algorithm=cast(EncryptionAlgorithmType, cpk.algorithm)
        )

    return None
