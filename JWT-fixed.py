#!/usr/bin/env python3
import os
import time
from pathlib import Path

import jwt

PRIVATE_KEY_FILE = os.getenv('QW_PRIVATE_KEY_FILE', 'ed25519-private.pem')
PROJECT_ID = os.getenv('QW_PROJECT_ID', 'your_project_id')
KEY_ID = os.getenv('QW_KEY_ID', 'your_key_id')
EXPIRE_SECONDS = int(os.getenv('JWT_EXPIRE_SECONDS', '900'))

private_key = Path(PRIVATE_KEY_FILE).read_text(encoding='utf-8')

payload = {
    'iat': int(time.time()) - 30,
    'exp': int(time.time()) + EXPIRE_SECONDS,
    'sub': PROJECT_ID,
}
headers = {
    'kid': KEY_ID,
}

encoded_jwt = jwt.encode(payload, private_key, algorithm='EdDSA', headers=headers)
print(encoded_jwt)
