import os
import zipfile
from pathlib import Path

assets_dir = Path(r"C:\Users\nishanth\.gemini\antigravity-ide\scratch\m-arch\test_assets")
assets_dir.mkdir(parents=True, exist_ok=True)

# 1. Create sample_project.zip
zip_path = assets_dir / "sample_project.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(
        "auth_service.py",
        "import hashlib\nimport jwt\n\ndef authenticate(user, password):\n    # Authentication logic\n    return jwt.encode({'user': user}, 'secret', algorithm='HS256')\n"
    )
    zf.writestr(
        "models/user.py",
        "class User:\n    def __init__(self, username, email):\n        self.username = username\n        self.email = email\n"
    )
    zf.writestr(
        "config.json",
        '{"service": "auth", "port": 8080, "rate_limit": 100}\n'
    )
print(f"Created {zip_path} ({zip_path.stat().st_size} bytes)")

# 2. Create individual test files for multi-file upload
files_dir = assets_dir / "multi_files"
files_dir.mkdir(parents=True, exist_ok=True)

(files_dir / "payment_gateway.py").write_text(
    "class PaymentGateway:\n    def process_charge(self, token, amount):\n        # Payment charge logic\n        return {'status': 'success', 'amount': amount}\n"
)
(files_dir / "routes.ts").write_text(
    "export function setupRoutes(app: any) {\n    app.post('/api/charge', (req, res) => res.json({ ok: true }));\n}\n"
)
(files_dir / "service_config.json").write_text(
    '{"service": "payments", "currency": "USD", "retry_count": 3}\n'
)
print("Created individual test files in", files_dir)
