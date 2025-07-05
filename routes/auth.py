# app/routes/auth.py - Simplified version without Flask-Login dependency
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import logging

# Set up logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Your FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000"

def login_required(f):
    """Simple decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This now checks for 'user_info' to be consistent with app.py
        if 'user_info' not in session or 'access_token' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with MFA support"""
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')
        
        logger.info(f"🔐 Login attempt for user: {username}")
        
        # Prepare login data for FastAPI
        login_data = {
            'username': username,
            'password': password
        }
        
        # Call FastAPI login endpoint
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        logger.info(f"🔐 Backend response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"🔐 Login response data: {data}")
            
            # --- FIXED: Store user data consistently in session['user_info'] ---
            session['access_token'] = data.get('access_token')
            session['user_id'] = data.get('user_id') # Keep for blueprint compatibility if needed
            
            # Create the user_info dictionary that the main app (app.py) expects
            session['user_info'] = {
                'user_id': data.get('user_id'),
                'username': data.get('username'),
                'full_name': data.get('full_name', ''),
                'is_admin': data.get('is_admin', False),
                'user_roles': data.get('user_roles', [])
            }
            # Ensure session is saved
            session.modified = True
            
            # Check if MFA is required
            if data.get('requires_mfa'):
                logger.info("🔒 MFA verification required")
                session['temp_token'] = data.get('access_token')
                session['awaiting_mfa'] = True
                return redirect(url_for('auth.mfa_verify'))
            
            # Check if MFA setup is required
            elif data.get('requires_mfa_setup'):
                logger.info("🔧 MFA setup required")
                session['needs_mfa_setup'] = True
                return redirect(url_for('auth.mfa_setup'))
            
            # Normal login success
            else:
                logger.info("✅ Login successful, no MFA required")
                flash(f'Welcome back, {data.get("username", "User")}!', 'success')
                return redirect(url_for('dashboard'))
        
        else:
            error_detail = "Invalid username or password"
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', error_detail)
            except:
                pass
            
            logger.warning(f"❌ Login failed: {error_detail}")
            flash(error_detail, 'error')
            return render_template('auth/login.html')
    
    except requests.exceptions.Timeout:
        logger.error("⏰ Login request timed out")
        flash('Login request timed out. Please try again.', 'error')
        return render_template('auth/login.html')
    
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Cannot connect to authentication service")
        flash('Cannot connect to authentication service. Please try again later.', 'error')
        return render_template('auth/login.html')
    
    except Exception as e:
        logger.error(f"💥 Unexpected error during login: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('auth/login.html')

@auth_bp.route('/mfa-setup', methods=['GET', 'POST'])
def mfa_setup():
    """Handle MFA setup for users who need it"""
    
    if request.method == 'GET':
        # Check if user is supposed to be setting up MFA
        if not session.get('needs_mfa_setup') and not session.get('access_token'):
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            logger.info("🔧 Loading MFA setup page")
            
            # Get access token from session
            access_token = session.get('access_token')
            if not access_token:
                logger.error("❌ No access token found for MFA setup")
                flash('Authentication error. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
            
            # Call FastAPI MFA setup endpoint
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info("🔧 Calling FastAPI MFA setup endpoint...")
            response = requests.post(
                f"{BACKEND_URL}/api/auth/mfa/setup",
                headers=headers,
                timeout=10
            )
            
            logger.info(f"🔧 MFA setup response status: {response.status_code}")
            
            if response.status_code == 200:
                mfa_data = response.json()
                logger.info("✅ MFA setup data received successfully")
                
                # Store the secret in session temporarily
                session['mfa_secret'] = mfa_data.get('secret')
                
                return render_template(
                    'auth/mfa_setup.html',
                    secret=mfa_data.get('secret'),
                    qr_code_url=mfa_data.get('qr_code_url')
                )
            
            else:
                error_detail = "Failed to generate MFA setup"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', error_detail)
                    logger.error(f"❌ MFA setup error: {error_detail}")
                except:
                    logger.error(f"❌ MFA setup HTTP error: {response.status_code}")
                
                flash('Error loading MFA setup. Please contact support.', 'error')
                return render_template('auth/mfa_setup_error.html', error=error_detail)
        
        except requests.exceptions.Timeout:
            logger.error("⏰ MFA setup request timed out")
            flash('MFA setup request timed out. Please try again.', 'error')
            return render_template('auth/mfa_setup_error.html', error="Request timed out")
        
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Cannot connect to MFA service")
            flash('Cannot connect to MFA service. Please try again later.', 'error')
            return render_template('auth/mfa_setup_error.html', error="Cannot connect to service")
        
        except Exception as e:
            logger.error(f"💥 Unexpected error in MFA setup: {str(e)}")
            flash('An unexpected error occurred during MFA setup.', 'error')
            return render_template('auth/mfa_setup_error.html', error=str(e))
    
    # This shouldn't be called via POST - setup verification is handled separately
    return redirect(url_for('auth.mfa_setup'))

@auth_bp.route('/mfa-setup/verify', methods=['POST'])
def verify_mfa_setup():
    """Verify and complete MFA setup"""
    
    try:
        secret = request.form.get('secret')
        mfa_code = request.form.get('mfa_code')
        
        # Validate inputs
        if not secret or not mfa_code:
            flash('Secret and MFA code are required.', 'error')
            return redirect(url_for('auth.mfa_setup'))
        
        # Validate MFA code format
        if not mfa_code.isdigit() or len(mfa_code) != 6:
            flash('Please enter a valid 6-digit code from your authenticator app.', 'error')
            return redirect(url_for('auth.mfa_setup'))
        
        # Verify the secret matches what we have in session
        session_secret = session.get('mfa_secret')
        if not session_secret or session_secret != secret:
            logger.error("❌ Secret mismatch in MFA setup verification")
            flash('Security error. Please restart the MFA setup process.', 'error')
            session.pop('mfa_secret', None)
            return redirect(url_for('auth.mfa_setup'))
        
        logger.info(f"🔒 Verifying MFA setup with code: {mfa_code}")
        
        # Get access token
        access_token = session.get('access_token')
        if not access_token:
            flash('Authentication error. Please log in again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Call FastAPI MFA verification endpoint
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        verification_data = {
            'secret': secret,
            'mfa_code': mfa_code
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/mfa/verify-setup",
            headers=headers,
            json=verification_data,
            timeout=10
        )
        
        logger.info(f"🔒 MFA verification response status: {response.status_code}")
        
        if response.status_code == 200:
            verification_result = response.json()
            backup_codes = verification_result.get('backup_codes', [])
            
            logger.info("✅ MFA setup completed successfully")
            
            # Clear temporary session data
            session.pop('needs_mfa_setup', None)
            session.pop('mfa_secret', None)
            
            # Show backup codes to user
            session['backup_codes'] = backup_codes
            flash('Two-factor authentication has been successfully enabled!', 'success')
            
            return render_template(
                'auth/mfa_backup_codes.html',
                backup_codes=backup_codes
            )
        
        else:
            error_detail = "Invalid verification code"
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', error_detail)
            except:
                pass
            
            logger.warning(f"❌ MFA verification failed: {error_detail}")
            flash(error_detail, 'error')
            return redirect(url_for('auth.mfa_setup'))
    
    except requests.exceptions.Timeout:
        logger.error("⏰ MFA verification request timed out")
        flash('Verification request timed out. Please try again.', 'error')
        return redirect(url_for('auth.mfa_setup'))
    
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Cannot connect to MFA service")
        flash('Cannot connect to MFA service. Please try again later.', 'error')
        return redirect(url_for('auth.mfa_setup'))
    
    except Exception as e:
        logger.error(f"💥 Unexpected error in MFA verification: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('auth.mfa_setup'))

@auth_bp.route('/mfa-verify', methods=['GET', 'POST'])
def mfa_verify():
    """Handle MFA verification for existing users"""
    
    if request.method == 'GET':
        # Check if user should be here
        if not session.get('awaiting_mfa'):
            return redirect(url_for('auth.login'))
        
        return render_template('auth/mfa_verify.html')
    
    try:
        mfa_code = request.form.get('mfa_code')
        
        if not mfa_code or not mfa_code.isdigit() or len(mfa_code) != 6:
            flash('Please enter a valid 6-digit code.', 'error')
            return render_template('auth/mfa_verify.html')
        
        # Get temporary token
        temp_token = session.get('temp_token')
        if not temp_token:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('auth.login'))
        
        logger.info(f"🔒 Verifying MFA code: {mfa_code}")
        
        # Call FastAPI MFA verification endpoint
        headers = {
            'Authorization': f'Bearer {temp_token}',
            'Content-Type': 'application/json'
        }
        
        verification_data = {
            'mfa_code': mfa_code
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/mfa/verify",
            headers=headers,
            json=verification_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user', {})
            
            # --- FIXED: Store user data consistently in session['user_info'] ---
            session['access_token'] = data.get('access_token')
            session['user_id'] = user_data.get('user_id')
            
            # Create the user_info dictionary that the main app (app.py) expects
            session['user_info'] = {
                'user_id': user_data.get('user_id'),
                'username': user_data.get('username'),
                'full_name': user_data.get('full_name', ''),
                'is_admin': user_data.get('is_admin', False),
                'user_roles': user_data.get('user_roles', [])
            }
            
            # Clear temporary MFA data and save session
            session.pop('temp_token', None)
            session.pop('awaiting_mfa', None)
            session.modified = True
            
            logger.info("✅ MFA verification successful")
            flash(f'Welcome back, {user_data.get("username", "User")}!', 'success')
            return redirect(url_for('dashboard'))
        
        else:
            error_detail = "Invalid authentication code"
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', error_detail)
            except:
                pass
            
            logger.warning(f"❌ MFA verification failed: {error_detail}")
            flash(error_detail, 'error')
            return render_template('auth/mfa_verify.html')
    
    except Exception as e:
        logger.error(f"💥 Error in MFA verification: {str(e)}")
        flash('An error occurred during verification. Please try again.', 'error')
        return render_template('auth/mfa_verify.html')

@auth_bp.route('/mfa-backup-codes/done')
def mfa_backup_codes_done():
    """Handle completion of backup codes viewing"""
    session.pop('backup_codes', None)
    flash('MFA setup is now complete. You can now access the portal.', 'success')
    return redirect(url_for('dashboard'))

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    logger.info(f"🚪 User logout: {session.get('username', 'Unknown')}")
    
    # Clear all session data
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

# Helper function to get current user info
def get_current_user():
    """Get current user information from session"""
    if 'user_id' in session and 'access_token' in session:
        return {
            'id': session['user_id'],
            'username': session['username'],
            'full_name': session.get('full_name', ''),
            'access_token': session['access_token']
        }
    return None
