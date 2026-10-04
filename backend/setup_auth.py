"""Add a random JWT secret to local .env without exposing it or replacing settings."""
import re
import secrets
from pathlib import Path

path = Path(__file__).resolve().parent / ".env"
if not path.exists():
    raise SystemExit("Create backend/.env from .env.example first.")
content = path.read_text(encoding="utf-8")
match = re.search(r"^JWT_SECRET=(.*)$", content, re.MULTILINE)
if match and match.group(1).strip().strip('\"\''):
    print("JWT_SECRET already exists; kept unchanged.")
else:
    line = "JWT_SECRET=" + secrets.token_urlsafe(48)
    content = re.sub(r"^JWT_SECRET=.*$", line, content, flags=re.MULTILINE) if match else content.rstrip() + "\n" + line + "\n"
    path.write_text(content, encoding="utf-8")
    print("JWT_SECRET generated in backend/.env. Do not commit this file.")
