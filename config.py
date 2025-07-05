# config.py - Configuration Settings
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    FASTAPI_BASE_URL = os.environ.get('FASTAPI_BASE_URL') or 'http://127.0.0.1:8000'
    SESSION_TYPE = 'filesystem'
