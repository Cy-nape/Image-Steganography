from extensions import db
from datetime import datetime, timezone
import uuid

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_synthetic = db.Column(db.Boolean, default=False)

    api_keys = db.relationship('ApiKey', backref='user', lazy=True, cascade='all, delete-orphan')
    encode_jobs = db.relationship('EncodeJob', backref='user', lazy=True, cascade='all, delete-orphan')

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False, unique=True, index=True)
    key_prefix = db.Column(db.String(8), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_synthetic = db.Column(db.Boolean, default=False)

class EncodeJob(db.Model):
    __tablename__ = 'encode_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_hash = db.Column(db.String(256), nullable=False, index=True)
    huffman_dict = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_synthetic = db.Column(db.Boolean, default=False)

class ExperimentRun(db.Model):
    __tablename__ = 'experiment_runs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image_name = db.Column(db.String(255), nullable=False)
    image_size_kb = db.Column(db.Float, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    algorithm = db.Column(db.String(100), nullable=False)
    message_length = db.Column(db.Integer, nullable=False)
    compression_ratio = db.Column(db.Float, nullable=True)
    encode_time_ms = db.Column(db.Float, nullable=True)
    decode_time_ms = db.Column(db.Float, nullable=True)
    psnr = db.Column(db.Float, nullable=True)
    success = db.Column(db.Boolean, default=True)
