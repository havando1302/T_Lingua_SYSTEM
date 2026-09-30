"""Explicit database initialization and interactive administrator recovery.

This module never creates predictable credentials. Run with --help for the
operator-only bootstrap and MFA enrollment workflows.
"""
import argparse
from getpass import getpass
import os
from pathlib import Path
import sys

# Allow both "python -m app.db.init_db" and the legacy script entry point.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def init_db():
    from app.db.database import engine, SessionLocal
    from app.db.models import SystemSetting
    from app.db.security_migration import init_security_schema

    result = init_security_schema(engine)
    defaults = [
        ("max_chars_per_request", "5000", "Maximum characters per translation"),
        ("enable_cache", "true", "Enable translation cache"),
        ("rate_limit_rpm", "60", "Maximum requests per minute"),
    ]
    with SessionLocal() as db:
        for key, value, description in defaults:
            if db.query(SystemSetting).filter(SystemSetting.key == key).first() is None:
                db.add(SystemSetting(key=key, value=value, description=description))
        db.commit()
    return result


def _new_password():
    password = getpass("New password (12+ characters, max 72 UTF-8 bytes): ")
    if password != getpass("Confirm password: "):
        raise ValueError("Passwords do not match")
    return password


def _enroll_mfa(user, db, provisioning_file):
    import pyotp
    from app.core.security import encrypt_mfa_secret, verify_user_mfa, revoke_user_sessions

    if provisioning_file:
        seed = pyotp.random_base32()
        # Validate encryption configuration before exposing a provisioning artifact.
        encrypted = encrypt_mfa_secret(seed)
        destination = Path(provisioning_file).expanduser().resolve()
        descriptor = os.open(str(destination), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(pyotp.TOTP(seed).provisioning_uri(name=user.username, issuer_name="T-Langua"))
            output.write("\n")
        print(f"Provisioning file created: {destination}")
        print("Import it locally into your authenticator, then securely remove the file.")
    else:
        seed = getpass("Authenticator Base32 secret (input hidden): ").replace(" ", "").upper()
        try:
            pyotp.TOTP(seed).now()
        except Exception as exc:
            raise ValueError("Invalid authenticator secret") from exc
        encrypted = encrypt_mfa_secret(seed)
    otp = getpass("Current six-digit authenticator code: ")
    if not pyotp.TOTP(seed).verify(otp, valid_window=1):
        raise ValueError("Authenticator verification failed; enrollment was not saved")
    user.mfa_secret_encrypted = encrypted
    user.mfa_enabled = True
    user.mfa_last_counter = -1
    db.flush()
    verify_user_mfa(user, otp, db)
    revoke_user_sessions(user, db)
    print("MFA enrollment completed. Existing sessions and API keys were revoked.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("init", "create-admin", "reset-password", "enroll-mfa"), default="init")
    parser.add_argument("--username", help="Account name; requested interactively when omitted")
    parser.add_argument("--role", choices=("admin", "superadmin"), default="superadmin")
    parser.add_argument("--provisioning-file", help="New private file for an MFA provisioning URI; never printed")
    args = parser.parse_args()
    if args.action != "init" and (not sys.stdin.isatty() or not sys.stderr.isatty()):
        parser.error("Credential operations require an interactive terminal")
    init_db()
    if args.action == "init":
        print("Database schema initialized. No default account or password was created.")
        return
    from app.db.database import SessionLocal
    from app.db.models import User
    from app.core.security import get_password_hash, revoke_user_sessions

    username = (args.username or input("Username: ")).strip()
    if not username or len(username) > 64:
        parser.error("Username must contain 1 to 64 characters")
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if args.action == "create-admin":
                if user is not None:
                    raise ValueError("Account already exists; use the explicit recovery action")
                user = User(username=username, password_hash=get_password_hash(_new_password()), role=args.role)
                db.add(user)
                db.commit()
                print("Administrator created. Enroll MFA before privileged login.")
            elif args.action == "reset-password":
                if user is None:
                    raise ValueError("Account not found")
                user.password_hash = get_password_hash(_new_password())
                user.is_active = True
                revoke_user_sessions(user, db)
                print("Password reset. Existing sessions and API keys were revoked.")
            elif args.action == "enroll-mfa":
                if user is None:
                    raise ValueError("Account not found")
                _enroll_mfa(user, db, args.provisioning_file)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
