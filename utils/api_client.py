# utils/api_client.py - API Client for FastAPI Backend
import requests
from flask import current_app, session
from utils.auth import get_auth_headers

class APIClient:
    @staticmethod
    def request(endpoint, method='GET', data=None, params=None):
        base_url = current_app.config['FASTAPI_BASE_URL']
        url = f"{base_url}/api{endpoint}"
        headers = get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )
        
        if response.status_code == 401:
            session.clear()
            raise Exception("Authentication required")
        
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def get(endpoint, params=None):
        return APIClient.request(endpoint, 'GET', params=params)
    
    @staticmethod
    def post(endpoint, data=None):
        return APIClient.request(endpoint, 'POST', data=data)
    
    @staticmethod
    def put(endpoint, data=None):
        return APIClient.request(endpoint, 'PUT', data=data)
    
    @staticmethod
    def delete(endpoint):
        return APIClient.request(endpoint, 'DELETE')
