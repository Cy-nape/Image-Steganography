import pytest
import tempfile
import os
import io

# Set environment variables for testing before importing app
db_fd, db_path = tempfile.mkstemp()
os.close(db_fd)  # close fd immediately; we only need the path
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['TESTING'] = 'true'

from app import app, db
from extensions import limiter

limiter.enabled = False

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['RATELIMIT_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        # Clean up database tables after each test to ensure isolation
        with app.app_context():
            db.drop_all()

def test_full_workflow(client):
    # 1. Register User A
    rv = client.post('/auth/register', json={'email': 'usera@test.com', 'password': 'password123'})
    assert rv.status_code == 201
    
    # 2. Login User A
    rv = client.post('/auth/login', json={'email': 'usera@test.com', 'password': 'password123'})
    assert rv.status_code == 200
    token_a = rv.get_json()['token']
    
    # 3. Create API Key for User A
    rv = client.post('/api-keys', json={'label': 'Test Key'}, headers={'Authorization': f'Bearer {token_a}'})
    assert rv.status_code == 201
    key_a = rv.get_json()['key']
    key_id_a = rv.get_json()['id']
    
    # 4. Register and Login User B
    client.post('/auth/register', json={'email': 'userb@test.com', 'password': 'password123'})
    rv = client.post('/auth/login', json={'email': 'userb@test.com', 'password': 'password123'})
    token_b = rv.get_json()['token']
    
    # 5. User B tries to fetch User A's keys (Isolation test)
    rv = client.get('/api-keys', headers={'Authorization': f'Bearer {token_b}'})
    assert len(rv.get_json()['api_keys']) == 0
    
    # User B tries to delete User A's key
    rv = client.delete(f'/api-keys/{key_id_a}', headers={'Authorization': f'Bearer {token_b}'})
    assert rv.status_code == 404
    
    # 6. Encode using User A's API Key
    with open('tests/fixtures/encoded_image.png', 'rb') as f:
        img_data = f.read()

    data = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'secret message',
        'pipeline': 'secure',
        'passphrase': 'testpassword'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'X-API-Key': key_a})
    assert rv.status_code == 200
    
    # 7. Decode using JWT
    encoded_img_data = rv.data
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png'),
        'passphrase': 'testpassword'
    }
    rv2 = client.post('/decode', data=data2, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token_a}'})
    assert rv2.status_code == 200
    assert rv2.get_json()['message'] == 'secret message'

    # 8. Revoke key A using User A's JWT
    rv = client.delete(f'/api-keys/{key_id_a}', headers={'Authorization': f'Bearer {token_a}'})
    assert rv.status_code == 200

    # 9. Ensure revoked key cannot be used
    data3 = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'another message'
    }
    rv = client.post('/encode', data=data3, content_type='multipart/form-data', headers={'X-API-Key': key_a})
    assert rv.status_code == 401

def test_encode_decode_basic_pipeline(client):
    client.post('/auth/register', json={'email': 'basic@test.com', 'password': 'password123'})
    rv = client.post('/auth/login', json={'email': 'basic@test.com', 'password': 'password123'})
    token = rv.get_json()['token']
    
    with open('tests/fixtures/encoded_image.png', 'rb') as f:
        img_data = f.read()

    data = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'basic message',
        'pipeline': 'basic'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv.status_code == 200
    
    encoded_img_data = rv.data
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png')
    }
    rv2 = client.post('/decode', data=data2, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv2.status_code == 200
    assert rv2.get_json()['message'] == 'basic message'

def test_encode_decode_secure_pipeline_valid(client):
    client.post('/auth/register', json={'email': 'secure@test.com', 'password': 'password123'})
    rv = client.post('/auth/login', json={'email': 'secure@test.com', 'password': 'password123'})
    token = rv.get_json()['token']
    
    with open('tests/fixtures/encoded_image.png', 'rb') as f:
        img_data = f.read()

    data = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'secure message',
        'pipeline': 'secure',
        'passphrase': 'correct_passphrase'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv.status_code == 200
    
    encoded_img_data = rv.data
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png'),
        'passphrase': 'correct_passphrase'
    }
    rv2 = client.post('/decode', data=data2, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv2.status_code == 200
    assert rv2.get_json()['message'] == 'secure message'

def test_encode_decode_secure_pipeline_invalid(client):
    client.post('/auth/register', json={'email': 'invalid@test.com', 'password': 'password123'})
    rv = client.post('/auth/login', json={'email': 'invalid@test.com', 'password': 'password123'})
    token = rv.get_json()['token']
    
    with open('tests/fixtures/encoded_image.png', 'rb') as f:
        img_data = f.read()

    data = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'secure message',
        'pipeline': 'secure',
        'passphrase': 'correct_passphrase'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv.status_code == 200
    encoded_img_data = rv.data
    
    # Test 1: Decode with wrong passphrase
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png'),
        'passphrase': 'wrong_passphrase'
    }
    rv2 = client.post('/decode', data=data2, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv2.status_code == 400
    assert 'error' in rv2.get_json()
    
    # Test 2: Decode with missing passphrase
    data3 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png')
    }
    rv3 = client.post('/decode', data=data3, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv3.status_code == 400
    assert 'error' in rv3.get_json()

def test_encode_decode_rgba(client):
    from PIL import Image
    client.post('/auth/register', json={'email': 'rgba@test.com', 'password': 'password123'})
    rv = client.post('/auth/login', json={'email': 'rgba@test.com', 'password': 'password123'})
    token = rv.get_json()['token']
    
    # Create an RGBA image in memory
    img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    data = {
        'image': (img_byte_arr, 'test_rgba.png'),
        'message': 'transparent message',
        'pipeline': 'basic'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv.status_code == 200
    
    # Read the output image and confirm it is RGB, not RGBA (alpha channel stripped by .convert('RGB'))
    encoded_img_data = rv.data
    out_img = Image.open(io.BytesIO(encoded_img_data))
    assert out_img.mode == 'RGB'
    
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png')
    }
    rv2 = client.post('/decode', data=data2, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'})
    assert rv2.status_code == 200
    assert rv2.get_json()['message'] == 'transparent message'
