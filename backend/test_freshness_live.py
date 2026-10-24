import os, io, json
import numpy as np
from PIL import Image
import urllib.request

# Create a synthetic fresh food image
arr = np.zeros((300,300,3), dtype=np.uint8)
arr[:150,:150] = [200, 50, 40]   # red tomato zone
arr[:150,150:] = [60, 160, 60]   # green lettuce
arr[150:,:150] = [160, 100, 60]  # brown bread
arr[150:,150:] = [220, 200, 50]  # yellow banana
img = Image.fromarray(arr, 'RGB')
img_path = 'test_synthetic.jpg'
img.save(img_path, quality=95)
print('Created', img_path)

boundary = '----TestBoundary'
with open(img_path, 'rb') as f:
    img_data = f.read()

body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="file"; filename="test_synthetic.jpg"\r\n'
    'Content-Type: image/jpeg\r\n\r\n'
).encode() + img_data + ('\r\n--' + boundary + '--\r\n').encode()

req = urllib.request.Request(
    'http://127.0.0.1:8001/api/v1/food/freshness?food_hint=mixed+food',
    data=body,
    method='POST',
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())

print('Status:', result['status'])
print('Freshness Score:', result['freshness_score'])
print('Freshness Label:', result['freshness_label'])
print('Safety Status:', result['safety_status'])
print('Detected Signs:', result['detected_signs'])
print('Food Category:', result['food_category'])
print('Features (subset):', {k:v for k,v in list(result['extracted_features'].items())[:6]})
print('Recs:', result['recommendations'][0][:80])
