from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


def _get_rest_session(client: VSphereClient) -> tuple[requests.Session, str]:
    """Create an authenticated REST session against the vCenter REST API."""
    settings = client._settings
    base_url = f"https://{settings.host}"
    session = requests.Session()
    session.verify = not settings.ignore_ssl
    resp = session.post(f"{base_url}/api/session", auth=(settings.user, settings.password))
    resp.raise_for_status()
    token = resp.json()
    session.headers.update({"vmware-api-session-id": token})
    return session, base_url


def register_security_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_identity_sources() -> dict[str, Any]:
        """List SSO (Single Sign-On) identity sources configured in vCenter.

        Returns each identity source including type, domain name, alias, and
        connection URL where available.
        """
        logger.info("list_identity_sources")

        session, base_url = _get_rest_session(client)

        # Primary endpoint: vCenter 7.0+ REST API
        resp = session.get(f"{base_url}/api/vcenter/identity/providers")
        if not resp.ok:
            # Fallback: try the older identity sources endpoint
            resp2 = session.get(f"{base_url}/api/vcenter/identity/info")
            if resp2.ok:
                data = resp2.json()
                return {
                    "status": "success",
                    "source_count": 1 if data else 0,
                    "identity_sources": [data] if data else [],
                    "note": "Retrieved from /api/vcenter/identity/info (limited detail)",
                }
            return {
                "status": "unavailable",
                "message": f"Identity sources endpoint returned {resp.status_code} — may not be available on this vCenter version",
                "identity_sources": [],
            }

        raw: list[Any] = resp.json() if isinstance(resp.json(), list) else []
        sources = []
        for entry in raw:
            if not isinstance(entry, dict):
                entry = {"id": str(entry)}
            sources.append({
                "id": entry.get("provider") or entry.get("id"),
                "type": entry.get("config_tag") or entry.get("type"),
                "domain_name": entry.get("domain_names") or entry.get("domain_name"),
                "alias": entry.get("alias"),
                "is_default": entry.get("is_default"),
            })

        return {
            "status": "success",
            "source_count": len(sources),
            "identity_sources": sources,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_sso_domain_info() -> dict[str, Any]:
        """Get SSO domain configuration including domain name and authentication settings.

        Tries multiple REST endpoints for compatibility across vCenter versions.
        """
        logger.info("get_sso_domain_info")

        session, base_url = _get_rest_session(client)

        # Try identity info endpoint first (vCenter 7+)
        resp = session.get(f"{base_url}/api/vcenter/identity/info")
        if resp.ok:
            data = resp.json()
            if isinstance(data, dict):
                return {
                    "status": "success",
                    "domain_name": data.get("domain") or data.get("domain_name"),
                    "tenant": data.get("tenant"),
                    "additional_info": data,
                }

        # Try the PSC / SSO domain via appliance endpoint
        resp2 = session.get(f"{base_url}/api/appliance/system/version")
        system_info: dict[str, Any] = {}
        if resp2.ok:
            system_info = resp2.json() if isinstance(resp2.json(), dict) else {}

        # Try identity providers for domain info
        resp3 = session.get(f"{base_url}/api/vcenter/identity/providers")
        providers: list[Any] = []
        if resp3.ok and isinstance(resp3.json(), list):
            providers = resp3.json()

        domain_names = []
        for p in providers:
            if isinstance(p, dict):
                dn = p.get("domain_names") or p.get("domain_name")
                if dn and dn not in domain_names:
                    domain_names.append(dn)

        if not domain_names and not system_info:
            return {
                "status": "unavailable",
                "message": "SSO domain info endpoints are not available on this vCenter version",
            }

        return {
            "status": "success",
            "domain_names": domain_names,
            "provider_count": len(providers),
            "system_version": system_info.get("version"),
            "system_build": system_info.get("build"),
        }

    @mcp.tool()
    @handle_tool_errors
    def list_sso_users() -> dict[str, Any]:
        """List users in the SSO domain (best-effort; may not be available on all versions).

        Returns local SSO accounts and any available identity source user listings.
        Full user enumeration from external identity sources (AD/LDAP) is typically
        not available via the REST API.
        """
        logger.info("list_sso_users")

        session, base_url = _get_rest_session(client)

        # Try local accounts endpoint (appliance local users, not SSO domain users)
        local_users: list[dict[str, Any]] = []
        resp = session.get(f"{base_url}/api/appliance/local-accounts")
        if resp.ok:
            raw = resp.json()
            if isinstance(raw, list):
                for entry in raw:
                    if isinstance(entry, str):
                        local_users.append({"username": entry, "source": "local_appliance"})
                    elif isinstance(entry, dict):
                        local_users.append({
                            "username": entry.get("username") or entry.get("name"),
                            "full_name": entry.get("fullname") or entry.get("full_name"),
                            "email": entry.get("email"),
                            "enabled": entry.get("enabled"),
                            "source": "local_appliance",
                        })

        # Best effort: check if SSO user list endpoint exists
        resp2 = session.get(f"{base_url}/api/vcenter/identity/users")
        sso_users: list[dict[str, Any]] = []
        if resp2.ok:
            raw2 = resp2.json()
            if isinstance(raw2, list):
                for entry in raw2:
                    if isinstance(entry, dict):
                        sso_users.append({
                            "username": entry.get("user") or entry.get("username"),
                            "domain": entry.get("domain"),
                            "source": "sso_domain",
                        })

        all_users = local_users + sso_users
        note = None
        if not sso_users:
            note = (
                "SSO domain user enumeration is not available via REST API. "
                "Showing local appliance accounts only. "
                "Use the vSphere Web Client or vSphere SSO API for full user listings."
            )

        return {
            "status": "success",
            "user_count": len(all_users),
            "users": all_users,
            **({"note": note} if note else {}),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_password_policy() -> dict[str, Any]:
        """Get the global password policy for local vCenter appliance accounts.

        Returns the maximum password age, minimum age, and warning period in days.
        """
        logger.info("get_password_policy")

        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/local-accounts/global-policy")
        if not resp.ok:
            return {
                "status": "unavailable",
                "message": f"Password policy endpoint returned {resp.status_code}",
                "http_status": resp.status_code,
            }

        data: dict[str, Any] = resp.json() if isinstance(resp.json(), dict) else {}

        return {
            "status": "success",
            "max_days": data.get("max_days"),
            "min_days": data.get("min_days"),
            "warn_days": data.get("warn_days"),
            "raw": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_password_policy(
        max_days: int = 90,
        min_days: int = 0,
        warn_days: int = 7,
    ) -> dict[str, Any]:
        """Set the global password policy for local vCenter appliance accounts.

        Args:
            max_days: Maximum number of days a password is valid before it must be changed (default 90).
            min_days: Minimum number of days before a password may be changed again (default 0).
            warn_days: Number of days before expiry that the user is warned (default 7).
        """
        logger.info("set_password_policy", max_days=max_days, min_days=min_days, warn_days=warn_days)

        if max_days < 0:
            return {"status": "error", "error": "max_days must be >= 0"}
        if min_days < 0:
            return {"status": "error", "error": "min_days must be >= 0"}
        if warn_days < 0:
            return {"status": "error", "error": "warn_days must be >= 0"}

        session, base_url = _get_rest_session(client)

        payload = {
            "max_days": max_days,
            "min_days": min_days,
            "warn_days": warn_days,
        }

        resp = session.put(f"{base_url}/api/appliance/local-accounts/global-policy", json=payload)
        if not resp.ok:
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            return {
                "status": "error",
                "error": f"Failed to set password policy (HTTP {resp.status_code})",
                "detail": err_detail,
            }

        return {
            "status": "success",
            "operation": "set_password_policy",
            "max_days": max_days,
            "min_days": min_days,
            "warn_days": warn_days,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_login_banner() -> dict[str, Any]:
        """Get the vCenter login banner (Message of the Day) shown on the login screen.

        Reads the advanced setting 'vpxd.motd' via the vCenter ServiceContent.
        """
        logger.info("get_login_banner")

        try:
            options = client.content.setting.QueryOptions("vpxd.motd")
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query vpxd.motd setting: {exc}"}

        if not options:
            return {
                "status": "success",
                "message": None,
                "note": "No login banner is configured (vpxd.motd is not set)",
            }

        banner_value = None
        for opt in options:
            if getattr(opt, "key", None) == "vpxd.motd":
                banner_value = getattr(opt, "value", None)
                break

        return {
            "status": "success",
            "key": "vpxd.motd",
            "message": banner_value,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_login_banner(message: str) -> dict[str, Any]:
        """Set the vCenter login banner (Message of the Day) displayed on the login screen.

        Updates the advanced setting 'vpxd.motd'. Set message to an empty string
        to clear the banner.

        Args:
            message: Banner text to display on the vCenter login page. Use an empty
                string "" to remove the existing banner.
        """
        logger.info("set_login_banner")

        from pyVmomi import vim

        option = vim.option.OptionValue(key="vpxd.motd", value=message)
        try:
            client.content.setting.UpdateValues([option])
        except Exception as exc:
            return {"status": "error", "error": f"Failed to update vpxd.motd setting: {exc}"}

        return {
            "status": "success",
            "operation": "set_login_banner",
            "message": message or "(cleared)",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_trust_authority_clusters() -> dict[str, Any]:
        """List vSphere Trust Authority (vTA) clusters configured in the environment.

        Trust Authority clusters provide attestation and key management services
        for workload protection. Returns cluster IDs and state where available.
        """
        logger.info("get_trust_authority_clusters")

        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/trusted-infrastructure/trusted-clusters")
        if resp.status_code == 404:
            return {
                "status": "unavailable",
                "message": "Trust Authority clusters endpoint is not available (requires vSphere 7.0+ with vTA license)",
                "clusters": [],
            }
        if not resp.ok:
            return {
                "status": "unavailable",
                "message": f"Trust Authority clusters endpoint returned {resp.status_code}",
                "clusters": [],
            }

        raw = resp.json()
        clusters: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, dict):
                    clusters.append({
                        "cluster": entry.get("cluster"),
                        "state": entry.get("state"),
                    })
                else:
                    clusters.append({"cluster": str(entry)})
        elif isinstance(raw, dict):
            clusters = [raw]

        return {
            "status": "success",
            "cluster_count": len(clusters),
            "trusted_clusters": clusters,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_trust_authority_attestation_services() -> dict[str, Any]:
        """List Trust Authority attestation services configured in the environment.

        Attestation services verify that ESXi hosts boot into a trusted state before
        they are permitted to access encrypted workloads.
        """
        logger.info("get_trust_authority_attestation_services")

        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/trusted-infrastructure/attestation/services")
        if resp.status_code == 404:
            return {
                "status": "unavailable",
                "message": "Attestation services endpoint is not available (requires vSphere 7.0+ with vTA license)",
                "services": [],
            }
        if not resp.ok:
            return {
                "status": "unavailable",
                "message": f"Attestation services endpoint returned {resp.status_code}",
                "services": [],
            }

        raw = resp.json()
        services: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, dict):
                    address_info = entry.get("address") or {}
                    services.append({
                        "service_id": entry.get("service"),
                        "address": address_info.get("hostname") if isinstance(address_info, dict) else address_info,
                        "port": address_info.get("port") if isinstance(address_info, dict) else None,
                        "group": entry.get("group"),
                        "trust_authority_cluster": entry.get("trust_authority_cluster"),
                    })
                else:
                    services.append({"service_id": str(entry)})
        elif isinstance(raw, dict):
            services = [raw]

        return {
            "status": "success",
            "service_count": len(services),
            "attestation_services": services,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_trust_authority_kms(
        provider_name: str,
        kms_address: str,
        kms_port: int = 5696,
    ) -> dict[str, Any]:
        """Configure a Trust Authority Key Management Server (KMS) provider.

        Registers a new KMS provider with the Trust Authority infrastructure.
        The KMS must be reachable from the Trust Authority cluster nodes and
        properly configured to accept connections from vSphere.

        Args:
            provider_name: Display name for the KMS provider.
            kms_address: Hostname or IP address of the KMS server.
            kms_port: KMIP port on the KMS server (default 5696).
        """
        logger.info(
            "configure_trust_authority_kms",
            provider_name=provider_name,
            kms_address=kms_address,
            kms_port=kms_port,
        )

        if kms_port < 1 or kms_port > 65535:
            return {"status": "error", "error": "kms_port must be between 1 and 65535"}

        session, base_url = _get_rest_session(client)

        # Attempt to register via the Trust Authority key providers endpoint
        endpoint = f"{base_url}/api/vcenter/trusted-infrastructure/trust-authority-clusters/kms/providers"

        payload = {
            "master_key_id": provider_name,
            "key_server": {
                "type": "KMIP",
                "kmip_key_server": {
                    "servers": [
                        {
                            "address": kms_address,
                            "port": kms_port,
                        }
                    ],
                    "username": None,
                },
                "description": provider_name,
            },
        }

        resp = session.post(endpoint, json=payload)

        if resp.status_code == 404:
            # Fallback: try the older crypto manager KMS endpoint
            legacy_endpoint = f"{base_url}/api/vcenter/crypto-manager/kms/providers"
            payload_legacy = {
                "provider": {
                    "provider_id": provider_name,
                    "servers": [
                        {
                            "address": kms_address,
                            "port": kms_port,
                        }
                    ],
                }
            }
            resp = session.post(legacy_endpoint, json=payload_legacy)
            if resp.status_code == 404:
                return {
                    "status": "unavailable",
                    "message": (
                        "Trust Authority KMS provider endpoints are not available "
                        "(requires vSphere 7.0+ with vTA license). "
                        "Use the vSphere Web Client or pyVmomi CryptoManager to configure KMS."
                    ),
                }

        if not resp.ok:
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            return {
                "status": "error",
                "error": f"Failed to configure Trust Authority KMS (HTTP {resp.status_code})",
                "detail": err_detail,
            }

        provider_id = None
        if resp.content:
            try:
                provider_id = resp.json()
            except Exception:
                pass

        return {
            "status": "success",
            "operation": "configure_trust_authority_kms",
            "provider_name": provider_name,
            "kms_address": kms_address,
            "kms_port": kms_port,
            "provider_id": provider_id,
        }
