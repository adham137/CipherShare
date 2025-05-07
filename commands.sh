python3 -m venv .venv
source .venv/bin/activate
deactivate
pip install colorama pytest rich pyfiglet pycryptodomec

pytest tests/unit/test_registry.py -q -s
pytest tests/unit/test_file_share_client.py -q -s

pytest tests/unit/test_command_factory.py -q -s
pytest tests/unit/test_download_strategy.py -q -s
pytest tests/unit/test_upload_strategy.py -q -s

pytest tests/unit/test_command_factory.py \
       tests/unit/test_download_strategy.py \
       tests/unit/test_upload_strategy.py -q -s

pytest tests/unit/test_fileshare_peer.py -q -s

pytest tests/unit/test_commands_enum.py -q -s
pytest tests/unit/test_crypto_utils.py -q -s
pytest tests/unit/test_ui.py -q -s

pytest -q
pytest -q -s

python src/central_registry/registry.py
python src/client/fileshare_client.py
