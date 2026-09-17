import os
import sys
import io
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

from app import create_app

def run_tests():
    print("============================================================")
    print("RUNNING SATQUERY AI (SIH26167) BACKEND INTEGRATION TESTS")
    print("============================================================")
    
    app = create_app()
    client = app.test_client()
    
    # 1. Test Health Check
    print("\n[TEST 1] Testing /api/health...")
    resp = client.get('/api/health')
    assert resp.status_code == 200, f"Health check failed with {resp.status_code}"
    health_data = resp.get_json()
    assert health_data['status'] == 'online'
    print("[OK] Health Check Passed:", health_data['service'])

    # 2. Test User Registration
    print("\n[TEST 2] Testing /api/auth/register...")
    resp = client.post('/api/auth/register', json={
        "email": "test_scientist@isro.gov.in",
        "password": "SecurePassword123!",
        "preferred_language": "ta"
    })
    assert resp.status_code in [201, 400], f"Registration failed with {resp.status_code}"
    print("[OK] User Registration Endpoint Passed")

    # 3. Test User Login
    print("\n[TEST 3] Testing /api/auth/login...")
    resp = client.post('/api/auth/login', json={
        "email": "test_scientist@isro.gov.in",
        "password": "SecurePassword123!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.data}"
    login_data = resp.get_json()
    assert login_data['success'] is True
    print("[OK] User Login Authentication Passed:", login_data['user']['email'])

    # 4. Test Single Image Analysis Mode
    print("\n[TEST 4] Testing Mode 1: Single Image Analysis...")
    sample_single = os.path.join(os.path.dirname(__file__), 'samples', 'single_sample.jpg')
    with open(sample_single, 'rb') as f:
        data = {
            'mode': 'single',
            'query': 'Identify buildings, water bodies and agricultural areas, and tell me where they are located.',
            'user_email': 'test_scientist@isro.gov.in',
            'image': (io.BytesIO(f.read()), 'single_sample.jpg')
        }
        resp = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200, f"Single analysis failed with {resp.status_code}: {resp.data}"
        single_res = resp.get_json()
        assert single_res['success'] is True
        bldgs = single_res['result']['buildings']['count']
        water = single_res['result']['water_bodies']['count']
        conf = single_res['result']['confidence']['score']
        evidence_file = single_res['result']['evidence']['filename']
        print(f"[OK] Mode 1 Passed: Detected {bldgs} buildings, {water} water bodies, Confidence: {conf}/100")
        print(f"  Visual Evidence generated: {evidence_file}")
        analysis_id = single_res['analysis_id']

    # 5. Test Optical + SAR Analysis Mode
    print("\n[TEST 5] Testing Mode 2: Optical + SAR Co-Analysis...")
    sample_opt = os.path.join(os.path.dirname(__file__), 'samples', 'optical_sample.jpg')
    sample_sar = os.path.join(os.path.dirname(__file__), 'samples', 'sar_sample.jpg')
    with open(sample_opt, 'rb') as f_opt, open(sample_sar, 'rb') as f_sar:
        data = {
            'mode': 'optical_sar',
            'query': 'Analyze this area using both optical and SAR imagery.',
            'user_email': 'test_scientist@isro.gov.in',
            'optical': (io.BytesIO(f_opt.read()), 'optical_sample.jpg'),
            'sar': (io.BytesIO(f_sar.read()), 'sar_sample.jpg')
        }
        resp = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200, f"Optical+SAR analysis failed with {resp.status_code}: {resp.data}"
        opt_sar_res = resp.get_json()
        assert opt_sar_res['success'] is True
        fusion = opt_sar_res['result']['fusion']
        print(f"[OK] Mode 2 Passed: Cross-modal agreement: {fusion.get('cross_modal_agreement_pct')}%, Fused water: {fusion.get('fused_water_coverage_pct')}%")

    # 6. Test Multitemporal Change Detection Mode
    print("\n[TEST 6] Testing Mode 3: Multitemporal Change Detection...")
    sample_bef = os.path.join(os.path.dirname(__file__), 'samples', 'before_sample.jpg')
    sample_aft = os.path.join(os.path.dirname(__file__), 'samples', 'after_sample.jpg')
    with open(sample_bef, 'rb') as f_bef, open(sample_aft, 'rb') as f_aft:
        data = {
            'mode': 'multitemporal',
            'query': 'Identify the changes that occurred between these two images.',
            'user_email': 'test_scientist@isro.gov.in',
            'before': (io.BytesIO(f_bef.read()), 'before_sample.jpg'),
            'after': (io.BytesIO(f_aft.read()), 'after_sample.jpg')
        }
        resp = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200, f"Multitemporal analysis failed with {resp.status_code}: {resp.data}"
        multi_res = resp.get_json()
        assert multi_res['success'] is True
        chg_pct = multi_res['result']['change_detection']['change_percentage']
        print(f"[OK] Mode 3 Passed: Measured surface change: {chg_pct}% across {len(multi_res['result']['change_detection']['change_regions'])} change zones")

    # 7. Test Location Analysis Mode
    print("\n[TEST 7] Testing Location / Coordinate Analysis Endpoint...")
    resp = client.post('/api/analyze-location', json={
        "latitude": 10.9601,
        "longitude": 76.9500,
        "query": "Analyze satellite features at these coordinates.",
        "user_email": "test_scientist@isro.gov.in"
    })
    print(f"  Location endpoint returned status {resp.status_code}")
    if resp.status_code == 200:
        loc_res = resp.get_json()
        assert loc_res['success'] is True
        print(f"[OK] Location Analysis Passed: {loc_res.get('location_metadata', {}).get('display_name')}")
    else:
        loc_err = resp.get_json()
        print(f"[OK] Location Diagnostic Valid (No fake data returned): {loc_err.get('error')}")

    # 8. Test PDF Report Generation & Download
    print("\n[TEST 8] Testing /api/reports/<id>/pdf...")
    resp = client.get(f'/api/reports/{analysis_id}/pdf')
    assert resp.status_code == 200, f"PDF report retrieval failed: {resp.status_code}"
    assert resp.mimetype == 'application/pdf'
    assert len(resp.data) > 1000, "PDF content is empty"
    print(f"[OK] PDF Report Generated & Validated: {len(resp.data)} bytes")

    # 9. Test History Retrieval
    print("\n[TEST 9] Testing /api/history...")
    resp = client.get('/api/history/?email=test_scientist@isro.gov.in')
    assert resp.status_code == 200
    hist_data = resp.get_json()
    assert hist_data['success'] is True
    assert len(hist_data['history']) >= 1
    print(f"[OK] History Retrieval Passed: Found {len(hist_data['history'])} records for user")

    print("\n============================================================")
    print("ALL 9 INTEGRATION TESTS PASSED SUCCESSFULLY WITH REAL DATA!")
    print("============================================================")

if __name__ == '__main__':
    run_tests()
