# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in vsphere-mcp, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: **security@example.com** (or open a private security advisory on GitHub)

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix release**: As soon as possible, depending on severity

## Security Considerations

### Credentials

- vSphere credentials are managed via environment variables (`VSPHERE_PASSWORD`)
- Credentials are never logged or included in error messages
- Use `VSPHERE_PASSWORD_FILE` for file-based secret management (planned)

### SSL/TLS

- SSL certificate verification is **enabled by default**
- `VSPHERE_IGNORE_SSL=true` disables verification (for development/self-signed certs only)
- **Never disable SSL verification in production**

### Destructive Operations

- All destructive operations require explicit `confirm=True`
- Operations are classified by danger level: low, medium, high, critical
- All operations are logged with structured logging (JSON format)

### Network Security

- The MCP server runs locally via stdio by default
- No ports are exposed unless SSE transport is explicitly configured
- vSphere API communication uses HTTPS

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Best Practices for Production Use

1. Use a dedicated vSphere service account with minimum required permissions
2. Enable SSL certificate verification
3. Run the MCP server in a restricted environment
4. Review structured logs regularly for unexpected operations
5. Consider network segmentation between the MCP server and vCenter
