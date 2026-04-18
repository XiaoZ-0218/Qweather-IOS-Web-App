#!/usr/bin/env python3
import os
import time
from pathlib import Path
from typing import Dict

import jwt
import requests
from flask import Flask, jsonify, request, send_file

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / 'index-backend-proxy.html'

app = Flask(__name__, static_folder=None)

QW_API_HOST = os.getenv('QW_API_HOST', '').strip()
QW_API_KEY = os.getenv('QW_API_KEY', '').strip()
QW_KEY_ID = os.getenv('QW_KEY_ID', '').strip()
QW_PROJECT_ID = os.getenv('QW_PROJECT_ID', '').strip()
QW_PRIVATE_KEY_FILE = os.getenv('QW_PRIVATE_KEY_FILE', '').strip()
QW_PRIVATE_KEY_TEXT = os.getenv('QW_PRIVATE_KEY_TEXT', '').strip()
INVITE_CODE = os.getenv('INVITE_CODE', '').strip()
JWT_EXPIRE_SECONDS = int(os.getenv('JWT_EXPIRE_SECONDS', '900'))
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '20'))
PORT = int(os.getenv('PORT', '8787'))


def require_host() -> None:
    if not QW_API_HOST:
        raise RuntimeError('Missing QW_API_HOST')


def load_private_key() -> str:
    if QW_PRIVATE_KEY_TEXT:
        return QW_PRIVATE_KEY_TEXT
    if QW_PRIVATE_KEY_FILE:
        return Path(QW_PRIVATE_KEY_FILE).read_text(encoding='utf-8')
    raise RuntimeError('Missing private key. Set QW_PRIVATE_KEY_FILE or QW_PRIVATE_KEY_TEXT.')


def console_ready() -> bool:
    return bool(QW_KEY_ID and QW_PROJECT_ID and (QW_PRIVATE_KEY_TEXT or QW_PRIVATE_KEY_FILE))


def build_jwt() -> str:
    if not console_ready():
        raise RuntimeError('Console API not configured. Need QW_KEY_ID, QW_PROJECT_ID and private key.')
    private_key = load_private_key()
    now = int(time.time())
    payload = {
        'sub': QW_PROJECT_ID,
        'iat': now - 30,
        'exp': now + JWT_EXPIRE_SECONDS,
    }
    headers = {'kid': QW_KEY_ID}
    return jwt.encode(payload, private_key, algorithm='EdDSA', headers=headers)


def weather_headers() -> Dict[str, str]:
    if not QW_API_KEY:
        raise RuntimeError('Missing QW_API_KEY')
    return {
        'Accept': 'application/json',
        'X-QW-Api-Key': QW_API_KEY,
    }


def console_headers() -> Dict[str, str]:
    token = build_jwt()
    return {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
    }


def proxy_get(path: str, *, query: Dict[str, str], console: bool = False):
    require_host()
    url = f'https://{QW_API_HOST}{path}'
    headers = console_headers() if console else weather_headers()
    resp = requests.get(url, headers=headers, params=query, timeout=HTTP_TIMEOUT)
    content_type = resp.headers.get('Content-Type', '')
    if 'application/json' in content_type:
        try:
            payload = resp.json()
        except Exception:
            payload = {'raw': resp.text}
    else:
        payload = {'raw': resp.text}
    return jsonify(payload), resp.status_code


@app.get('/')
def index():
    html = INDEX_FILE.read_text(encoding='utf-8')
    html = html.replace('__INVITE_CODE__', INVITE_CODE)
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.get('/api/health')
def health():
    return jsonify({
        'ok': True,
        'api_host': bool(QW_API_HOST),
        'weather_ready': bool(QW_API_HOST and QW_API_KEY),
        'console_ready': console_ready(),
        'console_auth': 'jwt' if console_ready() else 'not_configured',
    })


@app.get('/api/debug/jwt')
def debug_jwt():
    token = build_jwt()
    return jsonify({'ok': True, 'token': token, 'expires_in': JWT_EXPIRE_SECONDS})


@app.get('/api/v7/weather/now')
def api_weather_now():
    return proxy_get('/v7/weather/now', query=request.args.to_dict(flat=True))


@app.get('/api/v7/weather/24h')
def api_weather_24h():
    return proxy_get('/v7/weather/24h', query=request.args.to_dict(flat=True))


@app.get('/api/v7/weather/7d')
def api_weather_7d():
    return proxy_get('/v7/weather/7d', query=request.args.to_dict(flat=True))


@app.get('/api/v7/weather/3d')
def api_weather_3d():
    return proxy_get('/v7/weather/3d', query=request.args.to_dict(flat=True))


@app.get('/api/v7/weather/30d')
def api_weather_30d():
    return proxy_get('/v7/weather/30d', query=request.args.to_dict(flat=True))


@app.get('/api/v7/indices/1d')
def api_indices():
    return proxy_get('/v7/indices/1d', query=request.args.to_dict(flat=True))


@app.get('/api/weatheralert/v1/current/<lat>/<lon>')
def api_alerts(lat: str, lon: str):
    return proxy_get(f'/weatheralert/v1/current/{lat}/{lon}', query=request.args.to_dict(flat=True))


@app.get('/api/geo/v2/city/top')
def api_geo_top():
    return proxy_get('/geo/v2/city/top', query=request.args.to_dict(flat=True))


@app.get('/api/geo/v2/city/lookup')
def api_geo_lookup():
    return proxy_get('/geo/v2/city/lookup', query=request.args.to_dict(flat=True))


@app.get('/api/console/stats')
def api_console_stats():
    return proxy_get('/metrics/v1/stats', query=request.args.to_dict(flat=True), console=True)


@app.get('/api/console/finance')
def api_console_finance():
    return proxy_get('/finance/v1/summary', query=request.args.to_dict(flat=True), console=True)


@app.errorhandler(Exception)
def handle_error(err):
    code = getattr(err, 'code', 500)
    return jsonify({'ok': False, 'error': str(err)}), code


if __name__ == '__main__':
    print(f'WeatherOS backend running on http://127.0.0.1:{PORT}')
    app.run(host='0.0.0.0', port=PORT, debug=True)
