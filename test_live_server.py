import requests
import json
import os

BASE_URL = "http://127.0.0.1:5001"

def test_live_server():
    print("============================================================")
    print("VERIFYING LIVE RUNNING SERVER OVER HTTP SOCKETS (127.0.0.1:5000)")
    print("============================================================")
    
    # 1. Test Static HTML Delivery
    print("\n[HTTP TEST 1] GET / (index.html delivery)...")
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert "SATQUERY AI" in r.text
    assert "data-i18n" in r.text
    assert "css/style.css" in r.text
    assert "js/i18n.js" in r.text
    print(f"[OK] Index HTML delivered successfully ({len(r.text)} bytes)")

    # 2. Test CSS and JS Assets Delivery
    print("\n[HTTP TEST 2] GET CSS & JS static assets...")
    css_res = requests.get(f"{BASE_URL}/css/style.css")
    assert css_res.status_code == 200
    assert "--primary-cyan" in css_res.text
    print(f"[OK] CSS stylesheet loaded ({len(css_res.text)} bytes)")

    i18n_res = requests.get(f"{BASE_URL}/js/i18n.js")
    assert i18n_res.status_code == 200
    assert "translations" in i18n_res.text
    print(f"[OK] i18n multilingual script loaded ({len(i18n_res.text)} bytes)")

    # 3. Test Health API
    print("\n[HTTP TEST 3] GET /api/health...")
    health_res = requests.get(f"{BASE_URL}/api/health")
    assert health_res.status_code == 200
    h_json = health_res.json()
    assert h_json['status'] == 'online'
    print(f"[OK] Health check response: {h_json}")

    # 4. Test Single Analysis over HTTP FormData
    print("\n[HTTP TEST 4] POST /api/analyze (Single image mode)...")
    sample_path = "samples/single_sample.jpg"
    with open(sample_path, 'rb') as f:
        files = {'image': ('single_sample.jpg', f, 'image/jpeg')}
        data = {
            'mode': 'single',
            'query': 'Identify buildings, water bodies and agricultural areas, and tell me where they are located.',
            'user_email': 'live_test@isro.gov.in'
        }
        res = requests.post(f"{BASE_URL}/api/analyze", files=files, data=data)
        assert res.status_code == 200
        analysis_json = res.json()
        assert analysis_json['success'] is True
        print(f"[OK] Live Single Analysis: ID={analysis_json['analysis_id']}, Buildings={analysis_json['result']['buildings']['count']}, Confidence={analysis_json['result']['confidence']['score']}/100")
        aid = analysis_json['analysis_id']

    # 5. Test PDF Report Download over HTTP
    print("\n[HTTP TEST 5] GET /api/reports/<id>/pdf...")
    pdf_res = requests.get(f"{BASE_URL}/api/reports/{aid}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers.get('Content-Type') == 'application/pdf'
    assert len(pdf_res.content) > 5000
    print(f"[OK] PDF Report downloaded successfully over HTTP ({len(pdf_res.content)} bytes)")

    print("\n============================================================")
    print("ALL LIVE HTTP SOCKET TESTS PASSED!")
    print("============================================================")

if __name__ == '__main__':
    test_live_server()
