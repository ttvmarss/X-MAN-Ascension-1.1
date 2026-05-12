"""
Generate a self-signed SSL certificate for JARVIS (optional).
Run: python generate_cert.py
Produces cert.pem and key.pem in the current directory.
SSL is optional — JARVIS works fine over plain HTTP on localhost.
"""
import subprocess
import sys
import os


def try_openssl():
    try:
        subprocess.run(
            [
                "openssl", "req", "-x509",
                "-newkey", "rsa:2048",
                "-keyout", "key.pem",
                "-out", "cert.pem",
                "-days", "365",
                "-nodes",
                "-subj", "/CN=localhost",
            ],
            check=True,
            capture_output=True,
        )
        print("[OK] SSL certificate generated via openssl.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def try_cryptography():
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        with open("key.pem", "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))

        with open("cert.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print("[OK] SSL certificate generated via Python cryptography library.")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[WARN] cryptography library failed: {e}")
        return False


if __name__ == "__main__":
    print("Generating SSL certificate for JARVIS...")
    if try_openssl() or try_cryptography():
        print("cert.pem and key.pem created.")
        print("Restart JARVIS — it will now use wss:// (secure WebSocket).")
    else:
        print("[INFO] SSL generation skipped. JARVIS works fine without SSL on localhost.")
        print("       To enable SSL: install openssl or run 'pip install cryptography'")
