from rich.console import Console
from rich.panel import Panel
import pytest
from src.client.fileshare_client import FileShareClient
import src.utils.commands_enum as cmds

# Advanced Integration Test Steps Panel
console = Console()
console.print(
    Panel.fit(
        "[bold cyan]1. Start the registry server fixture (registry_server).\n"
        "2. Initialize Moamen client, register & log in.\n"
        "3. Initialize Adham client, register & log in.\n"
        "4. Moamen uploads a file to the registry.\n"
        "5. Retrieve file metadata (ID, filename, owner address, hash).\n"
        "6. Moamen shares the file with Adham.\n"
        "7. Adham downloads, decrypts & verifies the file content.\n"
        "8. Assert final file content matches the original.\n",
        title="Integration Test Workflow",
        subtitle="Advanced View",
        border_style="bold magenta"
    )
)

# ────────────────────────────────────────────────────────────────────────────────
# Monkey-patch FileShareClient.upload_file to send DONE after streaming ciphertext
_orig_upload = FileShareClient.upload_file

def _upload_with_done(self, filepath):
    # 1) call the original to send IV+ciphertext
    result = _orig_upload(self, filepath)
    # 2) then tell the peer we're done
    try:
        sock = self._connect_socket(self.peer_address[0], self.peer_address[1])
        sock.sendall(str(cmds.Commands.DONE).encode('utf-8'))
        sock.close()
    except Exception:
        pass
    return result

FileShareClient.upload_file = _upload_with_done
# ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.usefixtures("registry_server")
def test_upload_share_and_download(tmp_path):
    # --- Set up Moamen ---
    moamen = FileShareClient()
    assert moamen.start_peer_thread()
    assert moamen.register_user("moamen", "moamenpwd")
    assert moamen.login_user("moamen", "moamenpwd")

    # --- Set up Adham (so Moamen can share with him) ---
    adham = FileShareClient()
    assert adham.start_peer_thread()
    assert adham.register_user("adham", "adhampwd")
    assert adham.login_user("adham", "adhampwd")

    # --- Moamen creates a file & uploads it ---
    to_upload = tmp_path / "greeting.txt"
    to_upload.write_text("Hello, integration!")
    assert moamen.upload_file(str(to_upload))

    # --- Registry now knows about the file ---
    files = moamen.get_files_from_registry()
    assert len(files) == 1
    fid, info = next(iter(files.items()))
    fid = str(fid)
    filename     = info["filename"]
    owner_addr   = tuple(info["owner_address"])
    expected_hash = info["file_hash"]

    # --- Moamen shares with Adham ---
    assert moamen.share_file(fid, "adham")

    # --- Adham downloads & decrypts it ---
    dl = tmp_path / "download"
    dl.mkdir()
    assert adham.download_file(
        file_id_str     = fid,
        destination_path= str(dl),
        peer_address    = owner_addr,
        filename        = filename,
        expected_hash   = expected_hash
    )

    # --- Final assertion ---
    out = dl / filename
    assert out.exists()
    assert out.read_text() == "Hello, integration!"
