import pytest
import tempfile
import os
import io

# Set environment variables for testing before importing app
db_fd, db_path = tempfile.mkstemp()
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['TESTING'] = 'true'

from app import app, db
from models import User, ApiKey, EncodeJob

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    
    os.close(db_fd)
    os.unlink(db_path)

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
    with open('image/encoded_image.png', 'rb') as f:
        img_data = f.read()

    data = {
        'image': (io.BytesIO(img_data), 'test.png'),
        'message': 'secret message'
    }
    rv = client.post('/encode', data=data, content_type='multipart/form-data', headers={'X-API-Key': key_a})
    assert rv.status_code == 200
    
    # 7. Decode using JWT
    encoded_img_data = rv.data
    data2 = {
        'image': (io.BytesIO(encoded_img_data), 'encoded.png')
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
