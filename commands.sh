python3 -m venv .venv
source .venv/bin/activate
deactivate
pip install colorama pytest rich pyfiglet pycryptodomec

python src/central_registry/registry.py
python src/client/fileshare_client.py

# Unit testing
pytest tests/unit/test_registry.py -q -s
pytest tests/unit/test_file_share_client.py -q -s

pytest tests/unit/test_command_factory.py -q -s
pytest tests/unit/test_download_strategy.py -q -s
pytest tests/unit/test_upload_strategy.py -q -s

pytest tests/unit/test_fileshare_peer.py -q -s

pytest tests/unit/test_commands_enum.py -q -s
pytest tests/unit/test_crypto_utils.py -q -s

# integartion testing
pytest tests/integration/ -q -s

# test
pytest -q 
pytest -q -s # 




