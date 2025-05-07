# tests/conftest.py
import os, sys, threading, time, socket, pytest

# 1) Add project root and src/ to PYTHONPATH
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'src'))

# 2) Import & patch
import src.central_registry.registry as registry_mod
import src.client.fileshare_client as client_mod
from src.central_registry.registry import start_registry_server, save_registry_data, load_registry_data
from src.utils.config import Config

@pytest.fixture(scope="session", autouse=True)
def isolate_config(tmp_path_factory):
    # fresh registry_data.json
    data_dir = tmp_path_factory.mktemp("data")
    temp_json = data_dir / "registry_data.json"
    try: os.remove(temp_json)
    except OSError: pass

    # fresh shared_files dir
    shared_dir = tmp_path_factory.mktemp("shared")
    os.makedirs(shared_dir, exist_ok=True)

    # pick a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    # patch Config
    Config.REGISTRY_DATA_FILE = str(temp_json)
    Config.SHARED_FILES_DIR   = str(shared_dir)
    Config.REGISTRY_PORT      = port

    # patch registry module globals
    registry_mod.REGISTRY_DATA_FILE = Config.REGISTRY_DATA_FILE
    registry_mod.REGISTRY_PORT      = Config.REGISTRY_PORT
    registry_mod.REGISTRY_ADDRESS   = Config.REGISTRY_IP

    # patch client module globals
    client_mod.REGISTRY_PORT    = Config.REGISTRY_PORT
    client_mod.REGISTRY_ADDRESS = Config.REGISTRY_IP

@pytest.fixture(scope="session", autouse=True)
def registry_server(isolate_config):
    # load empty state, then fire up the registry
    load_registry_data()
    thread = threading.Thread(
        target=start_registry_server,
        kwargs={'address': registry_mod.REGISTRY_ADDRESS,
                'port':    registry_mod.REGISTRY_PORT},
        daemon=True
    )
    thread.start()
    time.sleep(1)   # allow bind/listen
    yield
    save_registry_data()
