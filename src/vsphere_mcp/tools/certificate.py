from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_rest_session(client: VSphereClient) -> tuple[requests.Session, str]:
    """Create a REST session using vSphere credentials."""
    settings = client._settings
    base_url = f"https://{settings.host}"
    session = requests.Session()
    session.verify = not settings.ignore_ssl
    resp = session.post(f"{base_url}/api/session", auth=(settings.user, settings.password))
    resp.raise_for_status()
    token = resp.json()
    session.headers.update({"vmware-api-session-id": token})
    return session, base_url


def _parse_days_remaining(date_str: str) -> int | None:
    """Parse an ISO 8601 / RFC 3339 date string and return days until that date."""
    if not date_str:
        return None
    from datetime import datetime, timezone

    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    dt: datetime | None = None
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    return (dt - now).days


def register_certificate_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_tls_certificate() -> dict[str, Any]:
        """Get vCenter TLS certificate information including subject, issuer, validity, thumbprint, and serial number."""
        logger.info("get_vcenter_tls_certificate")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/certificate-management/vcenter/tls")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        validity: dict[str, Any] = data.get("validity", {})
        not_after = validity.get("valid_to") or data.get("valid_to")
        not_before = validity.get("valid_from") or data.get("valid_from")

        days_remaining = _parse_days_remaining(not_after)

        return {
            "subject": data.get("subject_dn") or data.get("subject"),
            "issuer": data.get("issuer_dn") or data.get("issuer"),
            "not_before": not_before or validity.get("valid_from"),
            "not_after": not_after or validity.get("valid_to"),
            "days_remaining": days_remaining,
            "thumbprint": data.get("thumbprint"),
            "serial": data.get("serial"),
            "status": data.get("status"),
            "key_size": data.get("key_size"),
            "signature_algorithm": data.get("signature_algorithm"),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_tls_csr(key_size: int = 2048) -> dict[str, Any]:
        """Generate a Certificate Signing Request (CSR) for the vCenter TLS certificate.

        Args:
            key_size: RSA key size in bits. Defaults to 2048. Common values: 2048, 4096.
        """
        logger.info("get_vcenter_tls_csr", key_size=key_size)

        session, base_url = _get_rest_session(client)
        resp = session.get(
            f"{base_url}/api/vcenter/certificate-management/vcenter/tls-csr",
            params={"key_size": key_size},
        )
        if not resp.ok:
            resp2 = session.post(
                f"{base_url}/api/vcenter/certificate-management/vcenter/tls-csr",
                json={"key_size": key_size},
            )
            resp2.raise_for_status()
            data = resp2.json()
        else:
            data = resp.json()

        if isinstance(data, str):
            csr_pem = data
        else:
            csr_pem = data.get("csr") or data.get("cert") or data.get("csr_pem") or str(data)

        return {
            "csr": csr_pem,
            "key_size": key_size,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def renew_vcenter_tls_certificate() -> dict[str, Any]:
        """Renew the vCenter TLS certificate using the VMware Certificate Authority (VMCA).

        This replaces the current TLS certificate with a new one signed by VMCA.
        Services that depend on TLS may restart. Requires confirm=True to execute.
        """
        logger.info("renew_vcenter_tls_certificate")

        session, base_url = _get_rest_session(client)
        resp = session.post(
            f"{base_url}/api/vcenter/certificate-management/vcenter/tls?action=renew"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "renew_vcenter_tls_certificate",
            "message": "vCenter TLS certificate renewal initiated via VMCA.",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def replace_vcenter_tls_certificate(
        cert_chain: str,
        private_key: str,
    ) -> dict[str, Any]:
        """Replace the vCenter TLS certificate with a custom certificate.

        Args:
            cert_chain: PEM-encoded certificate chain (leaf cert first, then intermediates, then root).
            private_key: PEM-encoded private key matching the certificate.
        """
        logger.info("replace_vcenter_tls_certificate")

        session, base_url = _get_rest_session(client)
        payload = {
            "cert": cert_chain,
            "key": private_key,
        }
        resp = session.put(
            f"{base_url}/api/vcenter/certificate-management/vcenter/tls",
            json=payload,
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "replace_vcenter_tls_certificate",
            "message": "vCenter TLS certificate replaced successfully.",
        }

    @mcp.tool()
    @handle_tool_errors
    def list_trusted_root_certificates() -> dict[str, Any]:
        """List all trusted root CA certificates configured in vCenter."""
        logger.info("list_trusted_root_certificates")

        session, base_url = _get_rest_session(client)
        resp = session.get(
            f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains"
        )
        resp.raise_for_status()
        chains: list[Any] = resp.json() if isinstance(resp.json(), list) else []

        results: list[dict[str, Any]] = []
        for entry in chains:
            if isinstance(entry, dict):
                chain_id = entry.get("chain") or entry.get("alias") or entry.get("id")
            else:
                chain_id = str(entry)

            detail: dict[str, Any] = {}
            if chain_id:
                detail_resp = session.get(
                    f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains/{chain_id}"
                )
                if detail_resp.ok:
                    raw = detail_resp.json()
                    if isinstance(raw, dict):
                        detail = raw

            cert_chain_data = detail.get("cert_chain") or {}
            cert_list = cert_chain_data.get("cert_chain") or [] if isinstance(cert_chain_data, dict) else []

            results.append({
                "chain_id": chain_id,
                "alias": detail.get("alias") or (entry.get("alias") if isinstance(entry, dict) else None),
                "subject": detail.get("subject_dn") or detail.get("subject"),
                "issuer": detail.get("issuer_dn") or detail.get("issuer"),
                "not_after": detail.get("valid_to"),
                "thumbprint": detail.get("thumbprint"),
                "cert_count": len(cert_list),
            })

        return {
            "total": len(results),
            "trusted_root_certificates": results,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_trusted_root_certificate(
        cert_chain: str,
        alias: str = "",
    ) -> dict[str, Any]:
        """Add a trusted root CA certificate to vCenter.

        Args:
            cert_chain: PEM-encoded root CA certificate (or chain of certificates).
            alias: Optional human-readable alias for the certificate chain.
        """
        logger.info("add_trusted_root_certificate", alias=alias)

        session, base_url = _get_rest_session(client)
        payload: dict[str, Any] = {
            "cert_chain": {
                "cert_chain": [cert_chain],
            },
        }
        if alias:
            payload["alias"] = alias

        resp = session.post(
            f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains",
            json=payload,
        )
        resp.raise_for_status()

        chain_id = None
        if resp.content:
            try:
                chain_id = resp.json()
            except Exception:
                pass

        return {
            "status": "success",
            "operation": "add_trusted_root_certificate",
            "chain_id": chain_id,
            "alias": alias or None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def remove_trusted_root_certificate(chain_id: str) -> dict[str, Any]:
        """Remove a trusted root CA certificate from vCenter by its chain ID.

        Args:
            chain_id: The ID of the trusted root certificate chain to remove.
                      Use list_trusted_root_certificates to find chain IDs.
        """
        logger.info("remove_trusted_root_certificate", chain_id=chain_id)

        session, base_url = _get_rest_session(client)
        resp = session.delete(
            f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains/{chain_id}"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "remove_trusted_root_certificate",
            "chain_id": chain_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_certificate_expiry_status() -> dict[str, Any]:
        """Check expiry status for all vCenter certificates including TLS and trusted root CAs.

        Returns a summary with days until expiry for each certificate to help
        identify certificates that need renewal.
        """
        logger.info("get_certificate_expiry_status")

        session, base_url = _get_rest_session(client)

        tls_entry: dict[str, Any] = {}
        tls_resp = session.get(f"{base_url}/api/vcenter/certificate-management/vcenter/tls")
        if tls_resp.ok:
            tls_data: dict[str, Any] = tls_resp.json()
            validity = tls_data.get("validity", {})
            not_after = validity.get("valid_to") or tls_data.get("valid_to")
            not_before = validity.get("valid_from") or tls_data.get("valid_from")
            days_remaining = _parse_days_remaining(not_after)
            tls_entry = {
                "type": "vcenter_tls",
                "subject": tls_data.get("subject_dn") or tls_data.get("subject"),
                "issuer": tls_data.get("issuer_dn") or tls_data.get("issuer"),
                "not_before": not_before,
                "not_after": not_after,
                "days_remaining": days_remaining,
                "thumbprint": tls_data.get("thumbprint"),
                "expiry_status": _expiry_label(days_remaining),
            }

        root_entries: list[dict[str, Any]] = []
        chains_resp = session.get(
            f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains"
        )
        if chains_resp.ok:
            chains: list[Any] = chains_resp.json() if isinstance(chains_resp.json(), list) else []
            for entry in chains:
                if isinstance(entry, dict):
                    chain_id = entry.get("chain") or entry.get("alias") or entry.get("id")
                else:
                    chain_id = str(entry)

                if not chain_id:
                    continue

                detail_resp = session.get(
                    f"{base_url}/api/vcenter/certificate-management/vcenter/trusted-root-chains/{chain_id}"
                )
                if not detail_resp.ok:
                    continue
                raw = detail_resp.json()
                if not isinstance(raw, dict):
                    continue

                not_after_root = raw.get("valid_to")
                days_remaining_root = _parse_days_remaining(not_after_root)
                root_entries.append({
                    "type": "trusted_root",
                    "chain_id": chain_id,
                    "subject": raw.get("subject_dn") or raw.get("subject"),
                    "issuer": raw.get("issuer_dn") or raw.get("issuer"),
                    "not_before": raw.get("valid_from"),
                    "not_after": not_after_root,
                    "days_remaining": days_remaining_root,
                    "thumbprint": raw.get("thumbprint"),
                    "expiry_status": _expiry_label(days_remaining_root),
                })

        all_certs = ([tls_entry] if tls_entry else []) + root_entries
        critical = [c for c in all_certs if c.get("days_remaining") is not None and c["days_remaining"] < 30]
        warning = [c for c in all_certs if c.get("days_remaining") is not None and 30 <= c["days_remaining"] < 90]

        return {
            "total_certificates": len(all_certs),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "certificates": all_certs,
            "summary": {
                "critical": [c.get("subject") or c.get("chain_id") for c in critical],
                "warning": [c.get("subject") or c.get("chain_id") for c in warning],
            },
        }


def _expiry_label(days: int | None) -> str:
    """Return a human-readable expiry status label based on days remaining."""
    if days is None:
        return "unknown"
    if days < 0:
        return "expired"
    if days < 30:
        return "critical"
    if days < 90:
        return "warning"
    return "ok"
