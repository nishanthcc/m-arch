import io
import zipfile
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import init_db, async_session_maker
from app.db.models import Project, Source, SourceSnapshot
from app.services.ingestion.validator import validate_and_extract_archive, is_safe_path
from app.main import app
from httpx import AsyncClient, ASGITransport

async def run_upload_tests():
    print("=== Testing Upload Pipeline & Secure Ingestion ===")
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a test project for ZIP upload
        create_res = await client.post("/api/v1/projects", json={
            "name": "Test ZIP Upload Project",
            "description": "Integration test for ZIP upload"
        })
        assert create_res.status_code in (200, 201), f"Failed project creation: {create_res.text}"
        project_id = create_res.json()["id"]
        print(f"Created project {project_id}")

        # 2. Test uploading a valid ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("main.py", "def main():\n    print('Hello from ZIP')\n")
            zf.writestr("utils/helper.py", "def add(a, b):\n    return a + b\n")
            zf.writestr("README.md", "# ZIP Project\nIntegration test archive.\n")
        zip_bytes = zip_buffer.getvalue()

        upload_res = await client.post(
            f"/api/v1/projects/{project_id}/sources",
            files={"files": ("archive.zip", zip_bytes, "application/zip")}
        )
        assert upload_res.status_code == 201, f"Failed valid ZIP upload: {upload_res.text}"
        sources = upload_res.json()
        assert len(sources) == 3, f"Expected 3 sources, got {len(sources)}"
        file_paths = {s["file_path"] for s in sources}
        assert "main.py" in file_paths, "main.py missing"
        assert "utils/helper.py" in file_paths, "utils/helper.py missing"
        assert "README.md" in file_paths, "README.md missing"
        print(f"Successfully uploaded and extracted valid ZIP: {len(sources)} sources created with relative paths.")

        # Verify SourceSnapshot creation
        async with async_session_maker() as db:
            from sqlalchemy import select
            snap_stmt = select(SourceSnapshot).where(SourceSnapshot.project_id == project_id)
            snaps = (await db.execute(snap_stmt)).scalars().all()
            assert len(snaps) >= 1, "Snapshot not created for ZIP upload"
            assert snaps[0].snapshot_type == "zip_upload"
            print(f"Snapshot verified: {snaps[0].id} (type={snaps[0].snapshot_type}, hash={snaps[0].source_hash[:12]}...)")

        # 3. Test uploading a corrupt ZIP file
        corrupt_bytes = b"NOT_A_REAL_ZIP_HEADER_CORRUPTED"
        corrupt_res = await client.post(
            f"/api/v1/projects/{project_id}/sources",
            files={"files": ("corrupt.zip", corrupt_bytes, "application/zip")}
        )
        assert corrupt_res.status_code == 400, f"Expected 400 for corrupt ZIP, got {corrupt_res.status_code}"
        assert "not a valid ZIP archive" in corrupt_res.json()["detail"]
        print(f"Correctly rejected corrupt ZIP: {corrupt_res.json()['detail']}")

        # 4. Create a second project for multi-file upload
        create_res2 = await client.post("/api/v1/projects", json={
            "name": "Test Multi-File Project",
            "description": "Integration test for multiple files upload"
        })
        assert create_res2.status_code in (200, 201)
        project_id_2 = create_res2.json()["id"]

        # 5. Test uploading multiple files with relative paths (simulating folder upload)
        file1 = ("src/server.ts", b"export const server = () => console.log('started');\n", "text/plain")
        file2 = ("config/default.json", b'{"port": 8080, "host": "127.0.0.1"}\n', "application/json")
        file3 = ("docs/arch.md", b"# Architecture\nDocumentation of server.\n", "text/markdown")

        files_payload = [
            ("files", file1),
            ("files", file2),
            ("files", file3)
        ]

        upload_files_res = await client.post(
            f"/api/v1/projects/{project_id_2}/sources",
            files=files_payload
        )
        assert upload_files_res.status_code == 201, f"Failed multi-file upload: {upload_files_res.text}"
        sources2 = upload_files_res.json()
        assert len(sources2) == 3, f"Expected 3 sources, got {len(sources2)}"
        paths2 = {s["file_path"] for s in sources2}
        assert "src/server.ts" in paths2, "src/server.ts missing"
        assert "config/default.json" in paths2, "config/default.json missing"
        assert "docs/arch.md" in paths2, "docs/arch.md missing"
        print(f"Successfully uploaded {len(sources2)} individual source files with directory hierarchy preserved.")

        # 6. Test binary rejection / no valid sources
        binary_file = ("bad.exe", b"\x4d\x5a\x90\x00\x03\x00\x00\x00", "application/octet-stream")
        binary_res = await client.post(
            f"/api/v1/projects/{project_id_2}/sources",
            files=[("files", binary_file)]
        )
        assert binary_res.status_code == 400
        assert "No valid source files were accepted" in binary_res.json()["detail"]
        print(f"Correctly rejected binary file upload: {binary_res.json()['detail']}")

        # 7. Clean up test projects
        del1 = await client.delete(f"/api/v1/projects/{project_id}")
        assert del1.status_code == 204
        del2 = await client.delete(f"/api/v1/projects/{project_id_2}")
        assert del2.status_code == 204
        print("Cleaned up test projects successfully.")

    print("\nALL UPLOAD INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_upload_tests())
