#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Dict

import requests
from flask import Flask, jsonify, request, send_file

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / 'index-backend-proxy.html'

app = Flask(__name__, static_folder=None)

QW_API_HOST = os.getenv('QW_API_HOST', '').strip()
QW_API_KEY = os.getenv('QW_API_KEY', '').strip()
INVITE_CODE = os.getenv('INVITE_CODE', '').strip()
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '20'))
PORT = int(os.getenv('PORT', '8787'))


def require_host() -> None:
    if not QW_API_HOST:
        raise RuntimeError('Missing QW_API_HOST')


def weather_headers() -> Dict[str, str]:
    if not QW_API_KEY:
        raise RuntimeError('Missing QW_API_KEY')
    return {
        'Accept': 'application/json',
        'X-QW-Api-Key': QW_API_KEY,
    }


def proxy_get(path: str, *, query: Dict[str, str]):
    require_host()
    url = f'https://{QW_API_HOST}{path}'
    headers = weather_headers()
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


@app.get('/icon-192.png')
def app_icon():
    return send_file(BASE_DIR / 'icon-192.png', mimetype='image/png')


@app.get('/manifest.webmanifest')
def manifest():
    return jsonify({
        'name': 'WeatherOS Aurora',
        'short_name': 'WeatherOS',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#081120',
        'theme_color': '#081120',
        'icons': [
            {
                'src': '/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any maskable',
            },
        ],
    }), 200, {'Content-Type': 'application/manifest+json; charset=utf-8'}


@app.get('/api/health')
def health():
    return jsonify({
        'ok': True,
        'api_host': bool(QW_API_HOST),
        'weather_ready': bool(QW_API_HOST and QW_API_KEY),
    })


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


@app.errorhandler(Exception)
def handle_error(err):
    code = getattr(err, 'code', 500)
    return jsonify({'ok': False, 'error': str(err)}), code


if __name__ == '__main__':
    print(f'WeatherOS backend running on http://127.0.0.1:{PORT}')
    app.run(host='0.0.0.0', port=PORT, debug=False)
