"""
Network helpers: LAN IP discovery, SSL cert auto-generation, QR code.
Used at server startup so users (especially on phones) can connect quickly.
"""
import os
import socket
import datetime
from pathlib import Path


def get_lan_ip() -> str:
    """Return the LAN IP the server is reachable at (best guess)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No traffic actually sent; just used to pick the right interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def ensure_self_signed_cert(cert_path: str = "cert.pem", key_path: str = "key.pem") -> bool:
    """Generate a self-signed cert covering localhost + LAN IP if missing. Returns True if cert is usable."""
    if Path(cert_path).exists() and Path(key_path).exists():
        return True

    lan_ip = get_lan_ip()
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "JARVIS Local"),
        ])

        san_entries = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]
        try:
            san_entries.append(x509.IPAddress(ipaddress.ip_address(lan_ip)))
        except ValueError:
            pass

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365 * 5))
            .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[SSL] Self-signed cert generated for localhost + {lan_ip}")
        return True
    except ImportError:
        print("[SSL] cryptography not installed; running without HTTPS.")
        print("       (HTTPS is required for phone microphone access.)")
        return False
    except Exception as e:
        print(f"[SSL] Cert generation failed: {e}")
        return False


def render_qr_ascii(url: str) -> str:
    """Render a URL as an ASCII QR code so users can scan from phone."""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1, box_size=1)
        qr.add_data(url)
        qr.make(fit=True)
        from io import StringIO
        buf = StringIO()
        qr.print_ascii(out=buf, invert=True)
        return buf.getvalue()
    except ImportError:
        return f"(Install 'qrcode' for scannable QR: pip install qrcode)\n  URL: {url}"
    except Exception as e:
        return f"(QR render failed: {e})\n  URL: {url}"


def print_connection_banner(host: str, port: int, https: bool):
    """Print a friendly startup banner with localhost + LAN URLs + QR code."""
    lan_ip = get_lan_ip()
    proto = "https" if https else "http"
    ws_proto = "wss" if https else "ws"
    local_url = f"{proto}://localhost:{port}"
    lan_url = f"{proto}://{lan_ip}:{port}"

    print()
    print("=" * 64)
    print("  J.A.R.V.I.S — ready")
    print("=" * 64)
    print(f"  Desktop (this PC):  {local_url}")
    print(f"  Phone / LAN:        {lan_url}")
    print(f"  WebSocket:          {ws_proto}://{lan_ip}:{port}/ws")
    print()
    if not https:
        print("  WARNING: HTTPS disabled. iPhone microphone access requires HTTPS.")
        print("           Install 'cryptography' and restart to auto-generate certs.")
        print()
    else:
        print("  iPhone note: Safari will warn about the self-signed cert.")
        print("               Tap 'Show Details' → 'Visit Website' to accept.")
        print()
    print("  Scan this on your phone:")
    print()
    for line in render_qr_ascii(lan_url).splitlines():
        print("    " + line)
    print("=" * 64)
    print()
