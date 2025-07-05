# utils/auth.py - Enhanced Authentication Utilities with Admin Features
from functools import wraps
from flask import session, redirect, url_for, request, current_app, flash, jsonify
import requests
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth.login'))
        
        # Verify token is still valid
        try:
            headers = {'Authorization': f"Bearer {session['access_token']}"}
            response = requests.get(f"{current_app.config['FASTAPI_BASE_URL']}/api/auth/verify-token", headers=headers)
            if response.status_code != 200:
                session.clear()
                return redirect(url_for('auth.login'))
        except:
            session.clear()
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Enhanced decorator to ensure user has admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # First check session admin flag (faster)
        user_info = session.get('user_info', {})
        session_admin = user_info.get('is_admin', False)
        session_roles = user_info.get('user_roles', [])
        
        # Quick admin check from session
        if session_admin or any(role.lower() in ['admin', 'administrator', 'system_admin'] for role in session_roles):
            return f(*args, **kwargs)
        
        # Enhanced fallback: Check admin access with new verify endpoint
        headers = {'Authorization': f'Bearer {session["access_token"]}'}
        try:
            # Try the new verify-access endpoint first (if available)
            response = requests.get(f'{current_app.config["FASTAPI_BASE_URL"]}/api/admin/verify-access', headers=headers, timeout=10)
            if response.status_code == 200:
                admin_data = response.json()
                if admin_data.get('success') and admin_data.get('capabilities', {}).get('is_admin'):
                    # Update session with admin info for future requests
                    session['user_info']['is_admin'] = True
                    session['user_info']['admin_capabilities'] = admin_data.get('capabilities', {})
                    session['user_info']['user_roles'] = admin_data.get('user', {}).get('roles', [])
                    return f(*args, **kwargs)
            
            # Fallback to original stats endpoint check
            response = requests.get(f'{current_app.config["FASTAPI_BASE_URL"]}/api/admin/stats', headers=headers, timeout=10)
            if response.status_code == 200:
                # Update session with admin flag for future requests
                session['user_info']['is_admin'] = True
                return f(*args, **kwargs)
            else:
                flash('Admin access required.', 'error')
                return redirect(url_for('dashboard'))
                
        except requests.RequestException as e:
            logger.error(f"Error verifying admin access: {e}")
            flash('Unable to verify admin access.', 'error')
            return redirect(url_for('dashboard'))
        
    return decorated_function

def require_admin_permission(permission_name):
    """Decorator to require specific admin permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_admin_permission(permission_name):
                if request.is_json:
                    return jsonify({'error': f'Permission "{permission_name}" required'}), 403
                flash(f'You do not have permission to {permission_name.replace("_", " ")}', 'error')
                return redirect(url_for('admin.admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_admin_access(access_token):
    """Enhanced admin access check with capabilities"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        # Try the new verify-access endpoint first (if available)
        response = requests.get(f'{current_app.config["FASTAPI_BASE_URL"]}/api/admin/verify-access', headers=headers, timeout=10)
        if response.status_code == 200:
            admin_data = response.json()
            return {
                'is_admin': admin_data.get('success', False) and admin_data.get('capabilities', {}).get('is_admin', False),
                'user_roles': admin_data.get('user', {}).get('roles', []),
                'admin_capabilities': admin_data.get('capabilities', {}),
                'admin_level': admin_data.get('user', {}).get('admin_level', 'none')
            }
        
        # Fallback to original method
        response = requests.get(f'{current_app.config["FASTAPI_BASE_URL"]}/api/admin/stats', headers=headers, timeout=10)
        is_admin = response.status_code == 200
        
        # Get user roles for additional checking
        roles_response = requests.get(f'{current_app.config["FASTAPI_BASE_URL"]}/api/admin/roles', headers=headers, timeout=10)
        user_roles = []
        
        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            user_roles = roles_data.get('user_roles', [])
            # Additional admin check based on roles
            is_admin = is_admin or any(role.lower() in ['admin', 'administrator', 'system_admin'] for role in user_roles)
        
        return {
            'is_admin': is_admin,
            'user_roles': user_roles,
            'admin_capabilities': {'is_admin': is_admin},
            'admin_level': 'full' if is_admin else 'none'
        }
        
    except requests.RequestException as e:
        logger.error(f"Error checking admin access: {e}")
        return {
            'is_admin': False,
            'user_roles': [],
            'admin_capabilities': {},
            'admin_level': 'none'
        }

def handle_successful_login(user_data, access_token):
    """Enhanced login handler with admin capability checking"""
    session['access_token'] = access_token
    session['user_info'] = {
        'id': user_data.get('id'),
        'username': user_data.get('username'),
        'email': user_data.get('email'),
        'full_name': user_data.get('full_name'),
        'first_name': user_data.get('first_name'),
        'last_name': user_data.get('last_name')
    }
    
    # Enhanced admin access check
    admin_info = check_admin_access(access_token)
    session['user_info']['is_admin'] = admin_info['is_admin']
    session['user_info']['user_roles'] = admin_info['user_roles']
    session['user_info']['admin_capabilities'] = admin_info['admin_capabilities']
    session['user_info']['admin_level'] = admin_info['admin_level']
    
    logger.info(f"User {user_data.get('username')} logged in with admin status: {admin_info['is_admin']}")

def make_api_request(endpoint, method='GET', data=None, timeout=30):
    """Enhanced API request helper with better error handling"""
    if 'access_token' not in session:
        logger.warning("No access token available for API request")
        return None
        
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    url = f'{current_app.config["FASTAPI_BASE_URL"]}/api{endpoint}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=timeout)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Log admin API calls
        if endpoint.startswith('/admin/'):
            logger.info(f"Admin API: {method} {endpoint} - Status: {response.status_code}")
        
        return response
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {method} {url} - Error: {e}")
        return None

def get_user_info():
    """Get current user info from session"""
    return session.get('user_info')

def get_auth_headers():
    """Get authorization headers for API requests"""
    token = session.get('access_token')
    return {'Authorization': f"Bearer {token}"} if token else {}

def is_admin():
    """Quick check if current user is admin"""
    user_info = get_user_info()
    return user_info.get('is_admin', False) if user_info else False

def get_user_roles():
    """Get current user's roles"""
    user_info = get_user_info()
    return user_info.get('user_roles', []) if user_info else []

def get_admin_capabilities():
    """Get current user's admin capabilities"""
    user_info = get_user_info()
    return user_info.get('admin_capabilities', {}) if user_info else {}

def has_admin_permission(permission_name):
    """Check if current user has specific admin permission"""
    if not is_admin():
        return False
    
    capabilities = get_admin_capabilities()
    
    # If no specific capabilities are set, assume all permissions for admins
    if not capabilities or 'capabilities' not in capabilities:
        return True
    
    return capabilities.get('capabilities', {}).get(permission_name, False)

def get_admin_level():
    """Get admin level (none, limited, full, super)"""
    user_info = get_user_info()
    return user_info.get('admin_level', 'none') if user_info else 'none'

def refresh_admin_status():
    """Refresh admin status from API (useful after role changes)"""
    if 'access_token' not in session:
        return False
        
    try:
        admin_info = check_admin_access(session['access_token'])
        
        # Update session
        user_info = session.get('user_info', {})
        user_info.update({
            'is_admin': admin_info['is_admin'],
            'user_roles': admin_info['user_roles'],
            'admin_capabilities': admin_info['admin_capabilities'],
            'admin_level': admin_info['admin_level']
        })
        session['user_info'] = user_info
        
        logger.info(f"Refreshed admin status for user: {user_info.get('username')} - Admin: {admin_info['is_admin']}")
        return admin_info['is_admin']
        
    except Exception as e:
        logger.error(f"Error refreshing admin status: {e}")
        return False

# Admin permission constants for easy reference
class AdminPermissions:
    """Constants for admin permissions to avoid typos"""
    MANAGE_USERS = 'manage_users'
    MANAGE_FILTERS = 'manage_filters'
    VIEW_AUDIT_LOGS = 'view_audit_logs'
    MANAGE_SYSTEM_SETTINGS = 'manage_system_settings'
    ADMIN_ALL = 'admin_all'

# Context processor helpers for templates
def get_admin_context():
    """Get admin context for templates"""
    user_info = get_user_info()
    if not user_info:
        return {
            'is_admin': False,
            'admin_level': 'none',
            'admin_capabilities': {},
            'user_roles': [],
            'can_manage_users': False,
            'can_manage_filters': False,
            'can_view_audit_logs': False,
            'can_manage_system_settings': False
        }
    
    return {
        'is_admin': user_info.get('is_admin', False),
        'admin_level': user_info.get('admin_level', 'none'),
        'admin_capabilities': user_info.get('admin_capabilities', {}),
        'user_roles': user_info.get('user_roles', []),
        'can_manage_users': has_admin_permission(AdminPermissions.MANAGE_USERS),
        'can_manage_filters': has_admin_permission(AdminPermissions.MANAGE_FILTERS),
        'can_view_audit_logs': has_admin_permission(AdminPermissions.VIEW_AUDIT_LOGS),
        'can_manage_system_settings': has_admin_permission(AdminPermissions.MANAGE_SYSTEM_SETTINGS)
    }

# Flask error handler helpers
def handle_admin_error(error_code, message="Access denied"):
    """Handle admin-related errors consistently"""
    if request.is_json:
        return jsonify({'error': message}), error_code
    
    flash(message, 'error')
    
    if error_code == 401:
        return redirect(url_for('auth.login'))
    elif error_code == 403:
        return redirect(url_for('admin.admin_dashboard') if is_admin() else url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))

# Session management helpers
def clear_admin_session():
    """Clear admin-related session data"""
    user_info = session.get('user_info', {})
    user_info.pop('is_admin', None)
    user_info.pop('admin_capabilities', None)
    user_info.pop('admin_level', None)
    user_info.pop('user_roles', None)
    session['user_info'] = user_info

def logout_user():
    """Enhanced logout that clears all session data"""
    username = session.get('user_info', {}).get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    flash('You have been logged out successfully.', 'info')