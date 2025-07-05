# app.py - Complete working version with all routes including full loans functionality
from flask import Flask, app, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
import os
from datetime import datetime
import requests
from routes.auth import auth_bp
from routes.admin import admin_bp
import re

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['FASTAPI_BASE_URL'] = os.environ.get('FASTAPI_BASE_URL', 'http://127.0.0.1:8000')
    
    # Register the auth blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)    

    Session(app)

    # Add custom filters
    @app.template_filter('currency')
    def currency_filter(value):
        """Format value as currency"""
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """Format a date value for display in templates."""
        if value is None:
            return ''
        
        # Handle different input types
        if isinstance(value, str):
            try:
                # Try parsing ISO format first (e.g., "2025-06-22T18:33:09")
                if 'T' in value:
                    # Handle timezone info
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    elif '+' in value or value.count('-') > 2:
                        # Already has timezone info
                        pass
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    # Try standard date format
                    value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    # Try other common formats
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value  # Return original if parsing fails
        
        if isinstance(value, datetime):
            return value.strftime(format)
        
        return str(value)

    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M:%S'):
        """Format a datetime value for display in templates."""
        if value is None:
            return ''
        
        if isinstance(value, str):
            try:
                if 'T' in value:
                    # Handle timezone info
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Try alternative format
                    value = datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    return value
        
        if isinstance(value, datetime):
            return value.strftime(format)
        
        return str(value)

    @app.template_filter('time')
    def time_filter(value, format='%H:%M:%S'):
        """Format a time value for display in templates."""
        if value is None:
            return ''
        
        if isinstance(value, str):
            try:
                if 'T' in value:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
        
        if isinstance(value, datetime):
            return value.strftime(format)
        
        return str(value)
    
    # Add the format_phone filter
    def format_phone(phone_number):
        """Format phone number for display"""
        if not phone_number:
            return "Not provided"
        
        digits = re.sub(r'\D', '', str(phone_number))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) >= 7:
            if len(digits) <= 10:
                return f"{digits[:3]}-{digits[3:7]}" if len(digits) == 7 else f"({digits[:-7]}) {digits[-7:-4]}-{digits[-4:]}"
            else:
                return f"+{digits[:-10]} ({digits[-10:-7]}) {digits[-7:-4]}-{digits[-4:]}"
        else:
            return phone_number
        
    app.jinja_env.filters['format_phone'] = format_phone

    def get_auth_headers():
        """Get authorization headers from session"""
        access_token = session.get('access_token')
        if not access_token:
            return None
        return {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    def require_auth():
        if 'user_info' not in session:
            return redirect(url_for('auth.login'))
        return None

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    def dashboard():
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        # Get user info from session
        user_info = session.get('user_info', {})
        stats = {
            'username': user_info.get('username', 'Unknown'),
            'full_name': user_info.get('full_name', 'Unknown User')
        }
        
        return render_template('dashboard/index.html', stats=stats)

    # =============================================
    # ACCOUNTS ROUTES - Named to match templates
    # =============================================

    @app.route('/accounts')
    def accounts_index():
        """Main accounts listing page - matches url_for('accounts.index')"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get filter parameters from the form
            search = request.args.get('search', '')
            account_type = request.args.get('type', '')
            status = request.args.get('status', '')
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            skip = (page - 1) * per_page
            
            # Get access token from session
            access_token = session.get('access_token')
            if not access_token:
                flash('Authentication required', 'error')
                return redirect(url_for('auth.login'))
            
            # Prepare API request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build query parameters for FastAPI
            params = {
                'skip': skip,
                'limit': per_page
            }
            
            # Add filters if they exist
            if search:
                params['search'] = search
            if account_type:
                params['account_type'] = account_type
            if status:
                params['status'] = status
            
            # Call FastAPI backend
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.get(
                f"{fastapi_url}/api/accounts/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('items', [])
                total = data.get('total', 0)
                
                # Calculate pagination info
                total_pages = (total + per_page - 1) // per_page
                has_prev = page > 1
                has_next = page < total_pages
                
                print(f"Successfully fetched {len(accounts)} accounts from FastAPI")
                
                return render_template('accounts/index.html', 
                                    accounts=accounts,
                                    search=search,
                                    account_type=account_type,
                                    status=status,
                                    page=page,
                                    per_page=per_page,
                                    total=total,
                                    total_pages=total_pages,
                                    has_prev=has_prev,
                                    has_next=has_next)
            
            elif response.status_code == 401:
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
            
            else:
                print(f"FastAPI error: {response.status_code} - {response.text}")
                flash('Error loading accounts. Please try again.', 'error')
                return render_template('accounts/index.html', accounts=[], search=search, account_type=account_type, status=status)
        
        except requests.exceptions.ConnectionError:
            print("Could not connect to FastAPI backend")
            flash('Backend service unavailable. Please try again later.', 'error')
            return render_template('accounts/index.html', accounts=[], search=search, account_type=account_type, status=status)
        
        except requests.exceptions.Timeout:
            print("FastAPI request timed out")
            flash('Request timed out. Please try again.', 'error')
            return render_template('accounts/index.html', accounts=[], search=search, account_type=account_type, status=status)
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('accounts/index.html', accounts=[], search=search, account_type=account_type, status=status)

    @app.route('/accounts/new')
    def accounts_new():
        """Route for creating new accounts - matches url_for('accounts.new')"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        return render_template('accounts/new.html')

    @app.route('/accounts/create', methods=['POST'])
    def accounts_create():
        """Route for handling account creation - matches url_for('accounts.create')"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get form data
            account_data = {
                'company_name': request.form.get('company_name'),
                'account_type': request.form.get('account_type'),
                'primary_email': request.form.get('primary_email'),
                'home_phone': request.form.get('home_phone'),
                'cell_phone': request.form.get('cell_phone'),
                'work_phone': request.form.get('work_phone'),
                'street_address': request.form.get('street_address'),
                'city': request.form.get('city'),
                'state_province': request.form.get('state_province'),
                'postal_code': request.form.get('postal_code'),
                'country': request.form.get('country'),
                'notes': request.form.get('notes'),
                'tags': request.form.get('tags')
            }
            
            # Get access token
            access_token = session.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Call FastAPI backend
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.post(
                f"{fastapi_url}/api/accounts/",
                headers=headers,
                json=account_data,
                timeout=10
            )
            
            if response.status_code == 201:
                flash('Account created successfully!', 'success')
                return redirect(url_for('accounts_index'))
            else:
                flash('Error creating account. Please try again.', 'error')
                return render_template('accounts/new.html', **account_data)
        
        except Exception as e:
            print(f"Error creating account: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('accounts/new.html')

    @app.route('/accounts/<int:account_id>')
    def accounts_detail(account_id):
        """Route for viewing account details - matches url_for('accounts.detail', account_id=...)"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            access_token = session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            print(f"🔍 Loading account details for ID: {account_id}")
            
            # Load account details
            account_response = requests.get(
                f"{fastapi_url}/api/accounts/{account_id}",
                headers=headers,
                timeout=10
            )
            
            if account_response.status_code != 200:
                print(f"❌ Account API error: {account_response.status_code} - {account_response.text}")
                flash(f'Account not found (ID: {account_id}).', 'error')
                return redirect(url_for('accounts_index'))
            
            account = account_response.json()
            print(f"✅ Account loaded: {account.get('account_name', 'Unknown')}")
            
            # Initialize related data
            contacts = []
            loans = []
            assets = []
            cases = []
            
            # Load related data with multiple endpoint attempts
            # Try to load contacts
            contact_endpoints = [
                f"/api/contacts/?account_id={account_id}",
                f"/api/contacts?account_id={account_id}",
                f"/api/accounts/{account_id}/contacts"
            ]
            
            for endpoint in contact_endpoints:
                try:
                    contact_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if contact_response.status_code == 200:
                        contact_data = contact_response.json()
                        contacts = contact_data.get('items', contact_data) if isinstance(contact_data, dict) else contact_data
                        break
                except:
                    continue
            
            # Try to load loans
            loan_endpoints = [
                f"/api/loans/?account_id={account_id}",
                f"/api/loans?account_id={account_id}",
                f"/api/accounts/{account_id}/loans"
            ]
            
            for endpoint in loan_endpoints:
                try:
                    loan_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if loan_response.status_code == 200:
                        loan_data = loan_response.json()
                        loans = loan_data.get('items', loan_data) if isinstance(loan_data, dict) else loan_data
                        break
                except:
                    continue
            
            # Try to load assets
            asset_endpoints = [
                f"/api/assets/?account_id={account_id}",
                f"/api/assets?account_id={account_id}",
                f"/api/accounts/{account_id}/assets"
            ]
            
            for endpoint in asset_endpoints:
                try:
                    asset_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if asset_response.status_code == 200:
                        asset_data = asset_response.json()
                        assets = asset_data.get('items', asset_data) if isinstance(asset_data, dict) else asset_data
                        break
                except:
                    continue

            # Try to load cases
            case_endpoints = [
                f"/api/cases/?account_id={account_id}",
                f"/api/cases?account_id={account_id}",
                f"/api/accounts/{account_id}/cases"
            ]

            for endpoint in case_endpoints:
                try:
                    case_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if case_response.status_code == 200:
                        case_data = case_response.json()
                        cases = case_data.get('items', case_data) if isinstance(case_data, dict) else case_data
                        break
                except:
                    continue
            
            print(f"📊 Final data summary for account {account_id}:")
            print(f"   - Account: {account.get('account_name', 'Unknown')}")
            print(f"   - Contacts: {len(contacts)}")
            print(f"   - Loans: {len(loans)}")
            print(f"   - Assets: {len(assets)}")
            print(f"   - Cases: {len(cases)}")
            
            return render_template('accounts/detail.html', 
                                account=account, 
                                contacts=contacts or [], 
                                loans=loans or [], 
                                assets=assets or [],
                                cases=cases or [])
            
        except Exception as e:
            print(f"❌ Unexpected error for account {account_id}: {str(e)}")
            flash(f'Error loading account {account_id}: {str(e)}', 'error')
            return redirect(url_for('accounts_index'))
    
    @app.route('/accounts/<int:account_id>/edit')
    def accounts_edit(account_id):
        """Route for editing accounts - matches url_for('accounts.edit', account_id=...)"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            access_token = session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.get(
                f"{fastapi_url}/api/accounts/{account_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                account = response.json()
                return render_template('accounts/new.html', account=account)
            else:
                flash('Account not found.', 'error')
                return redirect(url_for('accounts_index'))
        
        except Exception as e:
            print(f"Error loading account for edit: {e}")
            flash('Error loading account for editing.', 'error')
            return redirect(url_for('accounts_index'))

    @app.route('/accounts/<int:account_id>/update', methods=['POST'])
    def accounts_update(account_id):
        """Route for updating accounts - matches url_for('accounts.update', account_id=...)"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get form data
            account_data = {
                'company_name': request.form.get('company_name'),
                'account_type': request.form.get('account_type'),
                'primary_email': request.form.get('primary_email'),
                'home_phone': request.form.get('home_phone'),
                'cell_phone': request.form.get('cell_phone'),
                'work_phone': request.form.get('work_phone'),
                'street_address': request.form.get('street_address'),
                'city': request.form.get('city'),
                'state_province': request.form.get('state_province'),
                'postal_code': request.form.get('postal_code'),
                'country': request.form.get('country'),
                'notes': request.form.get('notes'),
                'tags': request.form.get('tags')
            }
            
            access_token = session.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.put(
                f"{fastapi_url}/api/accounts/{account_id}",
                headers=headers,
                json=account_data,
                timeout=10
            )
            
            if response.status_code == 200:
                flash('Account updated successfully!', 'success')
                return redirect(url_for('accounts_detail', account_id=account_id))
            else:
                flash('Error updating account. Please try again.', 'error')
                return redirect(url_for('accounts_edit', account_id=account_id))
        
        except Exception as e:
            print(f"Error updating account: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('accounts_edit', account_id=account_id))

    # =============================================
    # LOANS ROUTES - COMPLETE IMPLEMENTATION
    # =============================================

    # Fixed loans route for app.py - Ensures loans is always a list, never None

    @app.route('/loans')
    def loans_index():
        """Loans list page - Fixed to prevent NoneType iteration errors"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        # Get filter parameters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        loan_type = request.args.get('type', '')
        financial_institution = request.args.get('financial_institution', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Initialize default values to prevent NoneType errors
        loans = []
        financial_institutions = []
        total = 0
        total_pages = 1
        has_prev = False
        has_next = False
        
        try:
            headers = get_auth_headers()
            if not headers:
                flash('Please log in to continue.', 'error')
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Build API query parameters for loans
            params = {
                'skip': (page - 1) * per_page,
                'limit': per_page
            }
            
            # Add optional filters only if they have values
            if search and search.strip():
                params['search'] = search.strip()
            if status and status.strip():
                params['loan_status'] = status.strip()
            if loan_type and loan_type.strip():
                params['loan_type'] = loan_type.strip()
            if financial_institution and financial_institution.strip():
                params['financial_institution'] = financial_institution.strip()
            
            print(f"🔍 DEBUG: Making loans API call with params: {params}")
            
            # Fetch loans from FastAPI with timeout
            response = requests.get(
                f"{fastapi_url}/api/loans/", 
                headers=headers, 
                params=params,
                timeout=30
            )
            
            print(f"🔍 DEBUG: Loans API response status: {response.status_code}")
            
            if response.status_code == 401:
                session.clear()
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
            elif response.status_code != 200:
                print(f"❌ Loans API error: {response.status_code} - {response.text}")
                flash(f'Error loading loans: HTTP {response.status_code}', 'error')
            else:
                # Parse the response safely
                try:
                    data = response.json()
                    print(f"🔍 DEBUG: Received data type: {type(data)}")
                    
                    # Handle paginated response from updated API
                    if isinstance(data, dict):
                        if 'items' in data:
                            loans = data['items'] or []  # Ensure it's never None
                            total = data.get('total', len(loans))
                        else:
                            # Handle case where dict doesn't have 'items' key
                            loans = []
                            total = 0
                    elif isinstance(data, list):
                        # Handle direct list response
                        loans = data
                        total = len(loans)
                    else:
                        # Handle unexpected response format
                        print(f"⚠️ WARNING: Unexpected response format: {type(data)}")
                        loans = []
                        total = 0
                    
                    print(f"🔍 DEBUG: Final loans count: {len(loans)}, total: {total}")
                    
                except Exception as json_error:
                    print(f"❌ JSON parsing error: {str(json_error)}")
                    flash('Error parsing loans data.', 'error')
                    loans = []
                    total = 0
            
            # Fetch financial institutions for filter dropdown
            try:
                print("🔍 DEBUG: Fetching financial institutions...")
                institutions_response = requests.get(
                    f"{fastapi_url}/api/loans/financial-institutions",
                    headers=headers,
                    timeout=10
                )
                if institutions_response.status_code == 200:
                    financial_institutions = institutions_response.json() or []
                    print(f"🔍 DEBUG: Got {len(financial_institutions)} financial institutions")
                else:
                    print(f"⚠️ Financial institutions API error: {institutions_response.status_code}")
                    financial_institutions = []
            except Exception as fi_error:
                print(f"⚠️ Error loading financial institutions: {str(fi_error)}")
                financial_institutions = []
            
            # Calculate pagination
            if total > 0:
                total_pages = max(1, (total + per_page - 1) // per_page)
                has_prev = page > 1
                has_next = page < total_pages
            else:
                total_pages = 1
                has_prev = False
                has_next = False
            
            print(f"🔍 DEBUG: Pagination - page: {page}, total_pages: {total_pages}, has_prev: {has_prev}, has_next: {has_next}")
            
        except requests.exceptions.Timeout:
            print("❌ Request timeout for loans")
            flash('Request timeout. Please try again.', 'error')
        except requests.exceptions.ConnectionError:
            print("❌ Connection error for loans")
            flash('Cannot connect to the backend service. Please try again later.', 'error')
        except requests.exceptions.RequestException as req_error:
            print(f"❌ Request error for loans: {str(req_error)}")
            flash(f'Network error loading loans: {str(req_error)}', 'error')
        except Exception as e:
            print(f"❌ Unexpected error in loans_index: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            flash('An unexpected error occurred while loading loans.', 'error')
        
        # CRITICAL: Ensure all variables are never None before rendering template
        if loans is None:
            loans = []
        if financial_institutions is None:
            financial_institutions = []
        if total is None:
            total = 0
        if total_pages is None:
            total_pages = 1
        
        print(f"🔍 DEBUG: Final template variables - loans: {len(loans)}, total: {total}, page: {page}")
        
        # Render template with safe default values
        return render_template('loans/index.html',
                            loans=loans,
                            financial_institutions=financial_institutions,
                            search=search,
                            status=status,
                            loan_type=loan_type,
                            financial_institution=financial_institution,
                            page=page,
                            per_page=per_page,
                            total_pages=total_pages,
                            total=total,
                            has_prev=has_prev,
                            has_next=has_next)

    @app.route('/loans/new')
    def loans_new():
        """New loan form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Load accounts and contacts for dropdowns
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            contacts_response = requests.get(f"{fastapi_url}/api/contacts/", headers=headers)
            
            accounts = []
            contacts = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                contacts = contacts_data.get('items', contacts_data) if isinstance(contacts_data, dict) else contacts_data
            
            return render_template('loans/form.html', loan=None, accounts=accounts, contacts=contacts)
            
        except requests.RequestException as e:
            flash(f'Error loading form data: {str(e)}', 'error')
            return render_template('loans/form.html', loan=None, accounts=[], contacts=[])

    @app.route('/loans/create', methods=['POST'])
    def loans_create():
        """Create new loan"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            loan_data = {
                'contract_number': request.form.get('contract_number'),
                'loan_type': request.form.get('loan_type'),
                'status': request.form.get('status', 'Active'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
                'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None
            }
            
            # Add financial fields if provided
            financial_fields = ['loan_amount', 'interest_rate', 'loan_term', 'monthly_payment', 'principal_balance']
            for field in financial_fields:
                value = request.form.get(field)
                if value:
                    try:
                        loan_data[field] = float(value)
                    except ValueError:
                        pass
            
            # Add date field
            if request.form.get('next_payment_date'):
                loan_data['next_payment_date'] = request.form.get('next_payment_date')
            
            # Remove None values
            loan_data = {k: v for k, v in loan_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.post(
                f"{fastapi_url}/api/loans/",
                headers=headers,
                json=loan_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            
            if response.status_code in [200, 201]:
                flash('Loan created successfully!', 'success')
                return redirect(url_for('loans_index'))
            else:
                flash('Error creating loan. Please try again.', 'error')
                return redirect(url_for('loans_new'))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('loans_new'))
        except requests.RequestException as e:
            flash(f'Error creating loan: {str(e)}', 'error')
            return redirect(url_for('loans_new'))

    # UPDATED AND ROBUST loans_detail route
    @app.route('/loans/<int:loan_id>')
    def loans_detail(loan_id):
        """Loan detail view that passes the full API response to the template."""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # 1. Fetch main loan data from the API
            response = requests.get(f"{fastapi_url}/api/loans/{loan_id}", headers=headers, timeout=10)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Loan not found', 'error')
                return redirect(url_for('loans_index'))
            elif response.status_code != 200:
                flash(f'Error loading loan details: {response.text}', 'error')
                return redirect(url_for('loans_index'))
            
            loan = response.json()

            # 2. PERFORM ALL CALCULATIONS IN PYTHON FOR TYPE SAFETY
            original_amount = float(loan.get('loan_amount', 0) or 0)
            principal_balance = float(loan.get('principal_balance', 0) or 0)
            past_due_amount = float(loan.get('past_due_amount', 0) or 0)
            past_due_fees = float(loan.get('past_due_fees', 0) or 0)

            # Calculate progress
            if original_amount > 0:
                amount_paid = original_amount - principal_balance
                progress_percent = round((amount_paid / original_amount * 100), 1)
            else:
                amount_paid = 0
                progress_percent = 0
            
            # Calculate total due
            total_due = past_due_amount + past_due_fees
            
            # Add the calculated values to the loan dictionary
            loan['amount_paid'] = amount_paid
            loan['progress_percent'] = progress_percent
            loan['total_due'] = total_due
            
            # 3. Initialize placeholders for related data
            account, primary_contact, secondary_contact = None, None, None
            assets, cases = [], []

            # 4. Fetch related data based on IDs from the loan object
            if loan.get('account_id'):
                try:
                    acc_resp = requests.get(f"{fastapi_url}/api/accounts/{loan['account_id']}", headers=headers, timeout=5)
                    if acc_resp.status_code == 200:
                        account = acc_resp.json()
                except requests.RequestException as e:
                    print(f"Warning: Could not fetch account {loan['account_id']}: {e}")

            contact_id_to_fetch = loan.get('primary_contact') or loan.get('contact_id')
            if contact_id_to_fetch:
                try:
                    pc_resp = requests.get(f"{fastapi_url}/api/contacts/{contact_id_to_fetch}", headers=headers, timeout=5)
                    if pc_resp.status_code == 200:
                        primary_contact = pc_resp.json()
                except requests.RequestException as e:
                    print(f"Warning: Could not fetch primary contact {contact_id_to_fetch}: {e}")
            
            if loan.get('secondary_contact'):
                try:
                    sc_resp = requests.get(f"{fastapi_url}/api/contacts/{loan['secondary_contact']}", headers=headers, timeout=5)
                    if sc_resp.status_code == 200:
                        secondary_contact = sc_resp.json()
                except requests.RequestException as e:
                    print(f"Warning: Could not fetch secondary contact {loan['secondary_contact']}: {e}")

            try:
                assets_resp = requests.get(f"{fastapi_url}/api/assets/?loan_id={loan_id}", headers=headers, timeout=5)
                if assets_resp.status_code == 200:
                    assets_data = assets_resp.json()
                    assets = assets_data.get('items', assets_data) if isinstance(assets_data, dict) else assets_data
            except requests.RequestException as e:
                print(f"Warning: Could not fetch assets for loan {loan_id}: {e}")

            try:
                cases_resp = requests.get(f"{fastapi_url}/api/cases/?loan_id={loan_id}", headers=headers, timeout=5)
                if cases_resp.status_code == 200:
                    cases_data = cases_resp.json()
                    cases = cases_data.get('items', cases_data) if isinstance(cases_data, dict) else cases_data
            except requests.RequestException as e:
                print(f"Warning: Could not fetch cases for loan {loan_id}: {e}")

            # 5. Render the template with all the fetched data
            return render_template('loans/detail.html', 
                                   loan=loan, 
                                   account=account, 
                                   primary_contact=primary_contact,
                                   secondary_contact=secondary_contact,
                                   assets=assets or [],
                                   cases=cases or [])

        except requests.RequestException as e:
            flash(f'Error connecting to backend: {e}', 'error')
            return redirect(url_for('loans_index'))
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred in loans_detail: {traceback.format_exc()}")
            flash('An unexpected error occurred while loading loan details.', 'error')
            return redirect(url_for('loans_index'))


    @app.route('/loans/<int:loan_id>/edit')
    def loans_edit(loan_id):
        """Edit loan form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Fetch loan details
            response = requests.get(f"{fastapi_url}/api/loans/{loan_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Loan not found', 'error')
                return redirect(url_for('loans_index'))
            elif response.status_code != 200:
                flash('Error loading loan', 'error')
                return redirect(url_for('loans_index'))
            
            loan = response.json()
            
            # Load accounts and contacts for dropdowns
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            contacts_response = requests.get(f"{fastapi_url}/api/contacts/", headers=headers)
            
            accounts = []
            contacts = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                contacts = contacts_data.get('items', contacts_data) if isinstance(contacts_data, dict) else contacts_data
            
            return render_template('loans/form.html', loan=loan, accounts=accounts, contacts=contacts)
            
        except requests.RequestException as e:
            flash(f'Error loading loan: {str(e)}', 'error')
            return redirect(url_for('loans_index'))

    @app.route('/loans/<int:loan_id>/update', methods=['POST'])
    def loans_update(loan_id):
        """Update loan"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            loan_data = {
                'contract_number': request.form.get('contract_number'),
                'loan_type': request.form.get('loan_type'),
                'status': request.form.get('status', 'Active'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
                'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None
            }
            
            # Add financial fields if provided
            financial_fields = ['loan_amount', 'interest_rate', 'loan_term', 'monthly_payment', 'principal_balance']
            for field in financial_fields:
                value = request.form.get(field)
                if value:
                    try:
                        loan_data[field] = float(value)
                    except ValueError:
                        pass
            
            # Add date field
            if request.form.get('next_payment_date'):
                loan_data['next_payment_date'] = request.form.get('next_payment_date')
            
            # Remove None values
            loan_data = {k: v for k, v in loan_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.put(
                f"{fastapi_url}/api/loans/{loan_id}",
                headers=headers,
                json=loan_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Loan not found', 'error')
                return redirect(url_for('loans_index'))
            elif response.status_code == 200:
                flash('Loan updated successfully!', 'success')
                return redirect(url_for('loans_detail', loan_id=loan_id))
            else:
                flash('Error updating loan. Please try again.', 'error')
                return redirect(url_for('loans_edit', loan_id=loan_id))
                
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('loans_edit', loan_id=loan_id))
        except requests.RequestException as e:
            flash(f'Error updating loan: {str(e)}', 'error')
            return redirect(url_for('loans_edit', loan_id=loan_id))

    @app.route('/loans/<int:loan_id>/delete', methods=['POST'])
    def loans_delete(loan_id):
        """Delete loan"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.delete(f"{fastapi_url}/api/loans/{loan_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Loan not found', 'error')
                return redirect(url_for('loans_index'))
            elif response.status_code == 200:
                flash('Loan deleted successfully!', 'success')
                return redirect(url_for('loans_index'))
            else:
                flash('Error deleting loan. Please try again.', 'error')
                return redirect(url_for('loans_detail', loan_id=loan_id))
                
        except requests.RequestException as e:
            flash(f'Error deleting loan: {str(e)}', 'error')
            return redirect(url_for('loans_detail', loan_id=loan_id))
        
        

    # Legacy loan route for backward compatibility
    @app.route('/loans_page')
    def loans_page():
        """Legacy redirect"""
        return redirect(url_for('loans_index'))

    # =============================================
    # CONTACTS ROUTES
    # =============================================

    @app.route('/contacts')
    def contacts_index():
        auth_check = require_auth()
        if auth_check:
            return auth_check

        try:
            # Get filter and pagination parameters from the URL
            search = request.args.get('search', '').strip()
            contact_type = request.args.get('type', '').strip()
            page = int(request.args.get('page', 1))
            per_page = 50  # Increased from 20 to match accounts page

            headers = get_auth_headers()
            if not headers:
                flash('Authentication required', 'error')
                return redirect(url_for('auth.login'))

            # Build query parameters for the API request
            params = {
                'skip': (page - 1) * per_page,
                'limit': per_page
            }
            
            # Add search parameter - make sure it's properly formatted
            if search:
                params['search'] = search
                print(f"🔍 Searching contacts for: '{search}'")
            
            # Add contact type filter
            if contact_type:
                params['contact_type'] = contact_type
                print(f"🏷️ Filtering by contact type: '{contact_type}'")

            # Call the FastAPI backend to get contacts
            fastapi_url = app.config['FASTAPI_BASE_URL']
            api_url = f"{fastapi_url}/api/contacts/"
            
            print(f"📡 Making API call to: {api_url}")
            print(f"📋 With parameters: {params}")
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=15  # Increased timeout
            )

            print(f"📊 API Response Status: {response.status_code}")

            # Handle the API response
            if response.status_code == 200:
                data = response.json()
                print(f"📄 Response data type: {type(data)}")
                
                # Handle both paginated response and direct list response
                if isinstance(data, dict):
                    # Paginated response format
                    contacts = data.get('items', [])
                    total = data.get('total', len(contacts))
                    print(f"📋 Paginated response: {len(contacts)} contacts, {total} total")
                elif isinstance(data, list):
                    # Direct list response format
                    contacts = data
                    total = len(contacts)
                    print(f"📋 Direct list response: {len(contacts)} contacts")
                else:
                    # Fallback
                    contacts = []
                    total = 0
                    print("❌ Unexpected response format")
                
                # Debug: Show first few contacts if search was performed
                if search and contacts:
                    print(f"🔍 Search results preview:")
                    for i, contact in enumerate(contacts[:3]):
                        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                        print(f"  {i+1}. {name} (ID: {contact.get('id')})")
                
                # Calculate pagination info
                total_pages = (total + per_page - 1) // per_page if total > 0 else 1
                has_prev = page > 1
                has_next = page < total_pages
                
                print(f"✅ Successfully fetched {len(contacts)} of {total} contacts from FastAPI")

                return render_template('contacts/index.html',
                                    contacts=contacts,
                                    search=search,
                                    contact_type=contact_type,
                                    page=page,
                                    per_page=per_page,
                                    total=total,
                                    total_pages=total_pages,
                                    has_prev=has_prev,
                                    has_next=has_next)

            elif response.status_code == 401:
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))

            else:
                try:
                    error_detail = response.json().get('detail', response.text)
                except:
                    error_detail = response.text
                print(f"❌ FastAPI error (contacts): {response.status_code} - {error_detail}")
                flash(f'Error loading contacts: {error_detail}', 'error')
                return render_template('contacts/index.html', 
                                    contacts=[], 
                                    search=search, 
                                    contact_type=contact_type,
                                    page=1,
                                    total_pages=1,
                                    total=0,
                                    has_prev=False,
                                    has_next=False)

        except requests.RequestException as e:
            print(f"❌ Could not connect to FastAPI backend for contacts: {e}")
            flash('Backend service unavailable. Please try again later.', 'error')
            return render_template('contacts/index.html', 
                                contacts=[], 
                                search=search or '', 
                                contact_type=contact_type or '',
                                page=1,
                                total_pages=1,
                                total=0,
                                has_prev=False,
                                has_next=False)

        except Exception as e:
            import traceback
            print(f"❌ Unexpected error in contacts_index: {traceback.format_exc()}")
            flash('An unexpected error occurred. Please check the logs.', 'error')
            return render_template('contacts/index.html', 
                                contacts=[], 
                                search=search or '', 
                                contact_type=contact_type or '',
                                page=1,
                                total_pages=1,
                                total=0,
                                has_prev=False,
                                has_next=False)

    @app.route('/contacts/new')
    def contacts_new():
        """New contact form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get account_id from query parameter if provided
            account_id = request.args.get('account_id')
            
            # You might want to load accounts for a dropdown
            headers = get_auth_headers()
            accounts = []
            
            if headers:
                try:
                    fastapi_url = app.config['FASTAPI_BASE_URL']
                    accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers, timeout=5)
                    if accounts_response.status_code == 200:
                        accounts_data = accounts_response.json()
                        accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
                except:
                    pass  # If loading accounts fails, just show empty form
            
            return render_template('contacts/form.html', contact=None, accounts=accounts, account_id=account_id)
        
        except Exception as e:
            print(f"Error loading new contact form: {e}")
            flash('Error loading form. Please try again.', 'error')
            return redirect(url_for('contacts_index'))

    @app.route('/contacts/create', methods=['POST'])
    def contacts_create():
        """Create new contact"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get form data
            contact_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'contact_type': request.form.get('contact_type'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None
            }
            
            # Remove None values
            contact_data = {k: v for k, v in contact_data.items() if v is not None and v != ''}
            
            access_token = session.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.post(
                f"{fastapi_url}/api/contacts/",
                headers=headers,
                json=contact_data,
                timeout=10
            )
            
            if response.status_code == 201:
                flash('Contact created successfully!', 'success')
                return redirect(url_for('contacts_index'))
            else:
                flash('Error creating contact. Please try again.', 'error')
                return render_template('contacts/form.html', contact=contact_data)
        
        except Exception as e:
            print(f"Error creating contact: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('contacts/form.html')

    @app.route('/contacts/<int:contact_id>')
    def contacts_detail(contact_id):
        """Contact detail page"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            access_token = session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            print(f"Loading contact details for ID: {contact_id}")  # Debug
            
            # Load contact details
            contact_response = requests.get(
                f"{fastapi_url}/api/contacts/{contact_id}",
                headers=headers,
                timeout=10
            )
            
            print(f"API response status: {contact_response.status_code}")  # Debug
            
            if contact_response.status_code != 200:
                flash('Contact not found.', 'error')
                return redirect(url_for('contacts_index'))
            
            contact = contact_response.json()
            print(f"Contact data: {contact}")  # Debug
            
            # Initialize related data
            related_account = None
            related_loans = []
            related_assets = []
            related_cases = []
            
            # Load related account if contact has account_id
            if contact.get('account_id'):
                try:
                    account_response = requests.get(f"{fastapi_url}/api/accounts/{contact['account_id']}", headers=headers, timeout=5)
                    if account_response.status_code == 200:
                        related_account = account_response.json()
                        print(f"Loaded related account: {related_account.get('account_name', 'Unknown')}")
                except Exception as e:
                    print(f"Error loading related account: {e}")
            
            # Try to load related loans with better filtering
            loan_endpoints = [
                f"/api/loans/?contact_id={contact_id}",
                f"/api/loans?contact_id={contact_id}",
                f"/api/contacts/{contact_id}/loans"
            ]
            
            for endpoint in loan_endpoints:
                try:
                    print(f"Trying loan endpoint: {fastapi_url}{endpoint}")
                    loan_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    print(f"Loan endpoint response: {loan_response.status_code}")
                    
                    if loan_response.status_code == 200:
                        loan_data = loan_response.json()
                        print(f"Raw loan data type: {type(loan_data)}")
                        
                        # Handle different response formats
                        if isinstance(loan_data, dict):
                            related_loans = loan_data.get('items', [])
                        elif isinstance(loan_data, list):
                            related_loans = loan_data
                        else:
                            related_loans = []
                        
                        print(f"Parsed {len(related_loans)} loans from {endpoint}")
                        
                        # Additional client-side filtering as backup
                        if related_loans:
                            # Filter loans that actually belong to this contact
                            filtered_loans = []
                            for loan in related_loans:
                                loan_contact_id = loan.get('contact_id')
                                print(f"Loan {loan.get('id', 'unknown')} contact_id: {loan_contact_id}, target: {contact_id}")
                                if loan_contact_id == contact_id:
                                    filtered_loans.append(loan)
                            
                            related_loans = filtered_loans
                            print(f"After filtering: {len(related_loans)} loans belong to contact {contact_id}")
                        
                        break
                except Exception as e:
                    print(f"Error loading loans from {endpoint}: {e}")
                    continue
            
            # If no loans found through contact_id, try through account relationship
            if 'related_loans' not in locals() or not related_loans:
                print("No loans found by contact_id, trying through account relationship...")
                if related_account and related_account.get('id'):
                    account_id = related_account['id']
                    account_loan_endpoints = [
                        f"/api/loans/?account_id={account_id}",
                        f"/api/loans?account_id={account_id}",
                        f"/api/accounts/{account_id}/loans"
                    ]
                    
                    for endpoint in account_loan_endpoints:
                        try:
                            print(f"Trying account loan endpoint: {fastapi_url}{endpoint}")
                            loan_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                            
                            if loan_response.status_code == 200:
                                loan_data = loan_response.json()
                                if isinstance(loan_data, dict):
                                    account_loans = loan_data.get('items', [])
                                elif isinstance(loan_data, list):
                                    account_loans = loan_data
                                else:
                                    account_loans = []
                                
                                print(f"Found {len(account_loans)} loans through account {account_id}")
                                
                                # Use account loans if we didn't find any through contact
                                if not related_loans:
                                    related_loans = account_loans
                                    print(f"Using account loans as fallback: {len(related_loans)} loans")
                                break
                        except Exception as e:
                            print(f"Error loading account loans from {endpoint}: {e}")
                            continue
            
            # If still no loans found, set empty list
            if 'related_loans' not in locals():
                related_loans = []
                print(f"No loans found for contact {contact_id} through any method")
            
            # Alternative: Load all loans and filter client-side (fallback)
            if not related_loans:
                try:
                    print("Final fallback: Loading all loans and filtering client-side")
                    all_loans_response = requests.get(f"{fastapi_url}/api/loans/", headers=headers, timeout=10)
                    if all_loans_response.status_code == 200:
                        all_loans_data = all_loans_response.json()
                        all_loans = all_loans_data.get('items', all_loans_data) if isinstance(all_loans_data, dict) else all_loans_data
                        
                        # Filter loans for this contact OR this contact's account
                        contact_account_id = related_account.get('id') if related_account else None
                        related_loans = []
                        
                        for loan in all_loans:
                            # Match by contact_id OR by account_id if contact has an account
                            if (loan.get('contact_id') == contact_id or 
                                (contact_account_id and loan.get('account_id') == contact_account_id)):
                                related_loans.append(loan)
                        
                        print(f"Client-side filtering found {len(related_loans)} loans for contact {contact_id}")
                except Exception as e:
                    print(f"Fallback filtering failed: {e}")
                    related_loans = []
            
            # Try to load related assets
            asset_endpoints = [
                f"/api/assets/?contact_id={contact_id}",
                f"/api/assets?contact_id={contact_id}",
                f"/api/contacts/{contact_id}/assets"
            ]
            
            for endpoint in asset_endpoints:
                try:
                    asset_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if asset_response.status_code == 200:
                        asset_data = asset_response.json()
                        related_assets = asset_data.get('items', asset_data) if isinstance(asset_data, dict) else asset_data
                        print(f"Loaded {len(related_assets)} related assets")
                        break
                except Exception as e:
                    print(f"Error loading assets from {endpoint}: {e}")
                    continue
            
            # Try to load related cases
            case_endpoints = [
                f"/api/cases/?contact_id={contact_id}",
                f"/api/cases?contact_id={contact_id}",
                f"/api/contacts/{contact_id}/cases"
            ]
            
            for endpoint in case_endpoints:
                try:
                    case_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                    if case_response.status_code == 200:
                        case_data = case_response.json()
                        related_cases = case_data.get('items', case_data) if isinstance(case_data, dict) else case_data
                        print(f"Loaded {len(related_cases)} related cases")
                        break
                except Exception as e:
                    print(f"Error loading cases from {endpoint}: {e}")
                    continue
            
            print("About to render template...")  # Debug
            print(f"Data summary: account={related_account is not None}, loans={len(related_loans)}, assets={len(related_assets)}, cases={len(related_cases)}")
            
            # Use different variable names to avoid conflict with namespace objects
            return render_template('contacts/detail.html', 
                                contact=contact, 
                                account=related_account,
                                loans=related_loans, 
                                assets=related_assets,
                                cases=related_cases)
        
        except Exception as e:
            import traceback
            print(f"Full error traceback: {traceback.format_exc()}")  # Better debug
            flash('Error loading contact details.', 'error')
            return redirect(url_for('contacts_index'))

    @app.route('/contacts/<int:contact_id>/edit')
    def contacts_edit(contact_id):
        """Edit contact form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Fetch contact details
            response = requests.get(f"{fastapi_url}/api/contacts/{contact_id}", headers=headers)
            
            if response.status_code != 200:
                flash('Contact not found', 'error')
                return redirect(url_for('contacts_index'))
            
            contact = response.json()
            
            # Load accounts for dropdown
            accounts = []
            try:
                accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
                if accounts_response.status_code == 200:
                    accounts_data = accounts_response.json()
                    accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            except:
                pass
            
            return render_template('contacts/form.html', contact=contact, accounts=accounts)
            
        except Exception as e:
            print(f"Error loading contact for edit: {e}")
            flash('Error loading contact for editing.', 'error')
            return redirect(url_for('contacts_index'))

    @app.route('/contacts/<int:contact_id>/update', methods=['POST'])
    def contacts_update(contact_id):
        """Update contact"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get form data
            contact_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'contact_type': request.form.get('contact_type'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None
            }
            
            # Remove None values
            contact_data = {k: v for k, v in contact_data.items() if v is not None and v != ''}
            
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.put(
                f"{fastapi_url}/api/contacts/{contact_id}",
                headers=headers,
                json=contact_data,
                timeout=10
            )
            
            if response.status_code == 200:
                flash('Contact updated successfully!', 'success')
                return redirect(url_for('contacts_detail', contact_id=contact_id))
            else:
                flash('Error updating contact. Please try again.', 'error')
                return redirect(url_for('contacts_edit', contact_id=contact_id))
                
        except Exception as e:
            print(f"Error updating contact: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('contacts_edit', contact_id=contact_id))

    # Legacy contacts route
    @app.route('/contacts_page')
    def contacts_page():
        """Legacy redirect"""
        return redirect(url_for('contacts_index'))

    # =============================================
    # ASSETS ROUTES - COMPLETE IMPLEMENTATION
    # =============================================

    # Update your Flask assets route in app.py with this fixed version

    @app.route('/assets')
    def assets_index():
        """Main assets listing page with pagination (loan matching temporarily disabled)"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get filter parameters from the form
            search = request.args.get('search', '').strip()
            make = request.args.get('make', '')
            status = request.args.get('status', '')
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            skip = (page - 1) * per_page
            
            # Get access token from session
            access_token = session.get('access_token')
            if not access_token:
                flash('Authentication required', 'error')
                return redirect(url_for('auth.login'))
            
            # Prepare API request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build query parameters for FastAPI
            params = {
                'skip': skip,
                'limit': per_page
            }
            
            if search:
                params['search'] = search
            if make:
                params['Make'] = make
            if status:
                params['status'] = status
            
            print(f"🔍 Assets search params: {params}")
            
            # Call FastAPI backend to get assets (with longer timeout)
            fastapi_url = app.config['FASTAPI_BASE_URL']
            try:
                response = requests.get(
                    f"{fastapi_url}/api/assets/",
                    headers=headers,
                    params=params,
                    timeout=30  # Increased timeout for assets call
                )
            except requests.exceptions.ReadTimeout:
                print("❌ Assets API timed out, trying with smaller page size")
                # Try with smaller page size if it times out
                params['limit'] = 25
                try:
                    response = requests.get(
                        f"{fastapi_url}/api/assets/",
                        headers=headers,
                        params=params,
                        timeout=30
                    )
                except requests.exceptions.ReadTimeout:
                    print("❌ Assets API still timing out with smaller page size")
                    flash('Database query is taking too long. Please try a more specific search.', 'warning')
                    return render_template('assets/index.html', 
                                        assets=[], 
                                        makes=[],
                                        search=search,
                                        make=make,
                                        status=status,
                                        page=1,
                                        total_pages=1,
                                        total=0,
                                        has_prev=False,
                                        has_next=False)
            
            print(f"📡 FastAPI response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and dictionary responses
                if isinstance(data, list):
                    assets = data
                    total = len(data)
                elif isinstance(data, dict):
                    assets = data.get('items', [])
                    total = data.get('total', len(assets))
                else:
                    assets = []
                    total = 0
                
                print(f"📊 Assets loaded: {len(assets)} of {total} total")
                
                # ===============================================
                # SMART LOAN MATCHING FOR PRINCIPAL BALANCE
                # Only fetch loans for the current assets being displayed
                # ===============================================
                
                print(f"💰 Starting targeted loan matching for {len(assets)} assets...")
                
                # Extract unique account IDs from current assets
                account_ids = list(set([asset.get('account_id') for asset in assets if asset.get('account_id')]))
                print(f"🎯 Found {len(account_ids)} unique account IDs to search: {account_ids[:5]}...")
                
                # Initialize all assets with None principal balance
                for asset in assets:
                    asset['principal_balance'] = None
                    asset['loan_principal_balance'] = None
                    asset['match_method'] = None
                
                if account_ids:
                    try:
                        # Try to get loans for these specific accounts only
                        matched_loans = []
                        successful_accounts = 0
                        
                        for account_id in account_ids:
                            try:
                                print(f"🔍 Searching loans for account {account_id}...")
                                
                                # Query loans API for this specific account
                                loans_response = requests.get(
                                    f"{fastapi_url}/api/loans/",
                                    headers=headers,
                                    params={
                                        'account_id': account_id,
                                        'limit': 50,  # Should be plenty per account
                                        'is_active': True
                                    },
                                    timeout=8  # Shorter timeout per account
                                )
                                
                                if loans_response.status_code == 200:
                                    loans_data = loans_response.json()
                                    
                                    # Handle both list and dict responses
                                    if isinstance(loans_data, dict):
                                        account_loans = loans_data.get('items', [])
                                    elif isinstance(loans_data, list):
                                        account_loans = loans_data
                                    else:
                                        account_loans = []
                                    
                                    if account_loans:
                                        matched_loans.extend(account_loans)
                                        successful_accounts += 1
                                        print(f"   ✅ Found {len(account_loans)} loans for account {account_id}")
                                    else:
                                        print(f"   ⚪ No loans found for account {account_id}")
                                
                                elif loans_response.status_code == 404:
                                    print(f"   ⚪ No loans found for account {account_id} (404)")
                                
                                else:
                                    print(f"   ❌ Error for account {account_id}: {loans_response.status_code}")
                            
                            except requests.exceptions.ReadTimeout:
                                print(f"   ⏱️ Timeout for account {account_id} - skipping")
                                continue
                            
                            except Exception as e:
                                print(f"   ❌ Exception for account {account_id}: {e}")
                                continue
                        
                        print(f"📊 Loan search complete:")
                        print(f"   - Searched {len(account_ids)} accounts")
                        print(f"   - Successfully got data from {successful_accounts} accounts")
                        print(f"   - Found {len(matched_loans)} total loans")
                        
                        if matched_loans:
                            # Show sample loan structure for debugging
                            sample_loan = matched_loans[0]
                            print(f"🔍 Sample loan structure:")
                            print(f"   Keys: {list(sample_loan.keys())}")
                            print(f"   Sample: id={sample_loan.get('id')}, account_id={sample_loan.get('account_id')}, principal_balance={sample_loan.get('principal_balance')}")
                            
                            # Create lookup for efficient matching
                            loans_by_account = {}
                            loans_by_asset_id = {}
                            
                            for loan in matched_loans:
                                # Group by account_id
                                if loan.get('account_id'):
                                    account_id = loan['account_id']
                                    if account_id not in loans_by_account:
                                        loans_by_account[account_id] = []
                                    loans_by_account[account_id].append(loan)
                                
                                # Direct asset_id matching (if available)
                                if loan.get('asset_id'):
                                    loans_by_asset_id[loan['asset_id']] = loan
                            
                            print(f"📋 Lookup tables created:")
                            print(f"   - Account lookup: {len(loans_by_account)} accounts")
                            print(f"   - Direct asset lookup: {len(loans_by_asset_id)} assets")
                            
                            # Match loans to assets
                            match_count = 0
                            
                            for asset in assets:
                                asset_id = asset.get('id')
                                asset_account_id = asset.get('account_id')
                                
                                matched_loan = None
                                match_method = None
                                
                                # Strategy 1: Direct asset-loan relationship
                                if asset_id in loans_by_asset_id:
                                    matched_loan = loans_by_asset_id[asset_id]
                                    match_method = "direct_asset"
                                
                                # Strategy 2: Account-based matching
                                elif asset_account_id in loans_by_account:
                                    account_loans = loans_by_account[asset_account_id]
                                    if account_loans:
                                        # Use loan with highest principal balance
                                        matched_loan = max(account_loans, key=lambda x: float(x.get('principal_balance', 0) or 0))
                                        match_method = "account_based"
                                
                                # Apply the match
                                if matched_loan:
                                    principal_balance = matched_loan.get('principal_balance')
                                    if principal_balance is not None:
                                        try:
                                            balance_float = float(principal_balance)
                                            asset['principal_balance'] = balance_float
                                            asset['loan_principal_balance'] = balance_float
                                            asset['matched_loan_id'] = matched_loan.get('id')
                                            asset['matched_loan_contract'] = matched_loan.get('contract_number')
                                            asset['match_method'] = match_method
                                            match_count += 1
                                            
                                            print(f"   💰 Asset {asset_id} → ${balance_float:,.2f} (via {match_method})")
                                        
                                        except (ValueError, TypeError) as e:
                                            print(f"   ❌ Invalid balance for asset {asset_id}: {principal_balance} ({e})")
                            
                            print(f"🎉 FINAL RESULT: {match_count} of {len(assets)} assets matched with principal balances")
                        
                        else:
                            print(f"⚪ No loans found for any of the displayed assets")
                    
                    except Exception as e:
                        print(f"❌ Error in loan matching process: {e}")
                        import traceback
                        print(f"❌ Traceback: {traceback.format_exc()}")
                
                else:
                    print(f"⚪ No account IDs found in current assets - cannot match loans")
                
                # Get unique makes for filter dropdown (with shorter timeout)
                makes = []
                try:
                    makes_response = requests.get(
                        f"{fastapi_url}/api/assets/",
                        headers=headers,
                        params={'skip': 0, 'limit': 100},  # Much smaller sample for makes
                        timeout=10
                    )
                    if makes_response.status_code == 200:
                        makes_data = makes_response.json()
                        
                        if isinstance(makes_data, list):
                            all_assets_for_makes = makes_data
                        elif isinstance(makes_data, dict):
                            all_assets_for_makes = makes_data.get('items', [])
                        else:
                            all_assets_for_makes = []
                        
                        makes = sorted(list(set(
                            asset.get('Make', '') for asset in all_assets_for_makes 
                            if asset.get('Make') and asset.get('Make') != 'None' and asset.get('Make').strip()
                        )))
                        
                except Exception as e:
                    print(f"Error getting makes: {e}")
                    makes = []
                
                # Calculate pagination info
                total_pages = max(1, (total + per_page - 1) // per_page)
                has_prev = page > 1
                has_next = page < total_pages
                
                return render_template('assets/index.html', 
                                    assets=assets,
                                    makes=makes,
                                    search=search,
                                    make=make,
                                    status=status,
                                    page=page,
                                    per_page=per_page,
                                    total=total,
                                    total_pages=total_pages,
                                    has_prev=has_prev,
                                    has_next=has_next)
            
            elif response.status_code == 401:
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
            
            else:
                print(f"FastAPI error: {response.status_code} - {response.text}")
                flash('Error loading assets. Please try again.', 'error')
                return render_template('assets/index.html', 
                                    assets=[], 
                                    makes=[],
                                    search=search,
                                    make=make,
                                    status=status,
                                    page=1,
                                    total_pages=1,
                                    total=0,
                                    has_prev=False,
                                    has_next=False)
        
        except ValueError as e:
            print(f"❌ Invalid parameter: {e}")
            flash('Invalid page parameter. Please try again.', 'error')
            return redirect(url_for('assets_index'))
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('assets/index.html', 
                                assets=[], 
                                makes=[],
                                search=search or '', 
                                make=make or '', 
                                status=status or '',
                                page=1,
                                total_pages=1,
                                total=0,
                                has_prev=False,
                                has_next=False)
    
    @app.route('/assets/new')
    def assets_new():
        """New asset form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Load accounts for dropdown
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            
            accounts = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            # Get account_id from query parameter if provided
            account_id = request.args.get('account_id')
            
            return render_template('assets/form.html', asset=None, accounts=accounts, account_id=account_id)
            
        except requests.RequestException as e:
            flash(f'Error loading form data: {str(e)}', 'error')
            return render_template('assets/form.html', asset=None, accounts=[])

    @app.route('/assets/create', methods=['POST'])
    def assets_create():
        """Create new asset"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            asset_data = {
                'Year': int(request.form.get('Year')) if request.form.get('Year') else None,
                'Make': request.form.get('Make'),
                'Model': request.form.get('Model'),
                'VIN': request.form.get('VIN'),
                'mileage': int(request.form.get('mileage')) if request.form.get('mileage') else None,
                'color': request.form.get('color'),
                'status': request.form.get('status', 'Active'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None
            }
            
            # Add financial fields if provided
            financial_fields = ['value', 'purchase_price', 'loan_balance']
            for field in financial_fields:
                value = request.form.get(field)
                if value:
                    try:
                        asset_data[field] = float(value)
                    except ValueError:
                        pass
            
            # Add other fields
            other_fields = ['condition', 'location', 'license_plate', 'insurance_company', 'notes']
            for field in other_fields:
                value = request.form.get(field)
                if value:
                    asset_data[field] = value
            
            # Add date fields
            date_fields = ['purchase_date', 'registration_date', 'insurance_expiry']
            for field in date_fields:
                value = request.form.get(field)
                if value:
                    asset_data[field] = value
            
            # Remove None values
            asset_data = {k: v for k, v in asset_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.post(
                f"{fastapi_url}/api/assets/",
                headers=headers,
                json=asset_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            
            if response.status_code in [200, 201]:
                flash('Asset created successfully!', 'success')
                return redirect(url_for('assets_index'))
            else:
                flash('Error creating asset. Please try again.', 'error')
                return redirect(url_for('assets_new'))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('assets_new'))
        except requests.RequestException as e:
            flash(f'Error creating asset: {str(e)}', 'error')
            return redirect(url_for('assets_new'))

    @app.route('/assets/<int:asset_id>')
    def assets_detail(asset_id):
        """Asset detail page with improved loan and case matching"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            access_token = session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            print(f"🔍 DEBUG: Loading asset details for ID: {asset_id}")
            
            # Load asset details
            asset_response = requests.get(
                f"{fastapi_url}/api/assets/{asset_id}",
                headers=headers,
                timeout=10
            )
            
            if asset_response.status_code != 200:
                print(f"❌ Asset API error: {asset_response.status_code} - {asset_response.text}")
                flash(f'Asset not found (ID: {asset_id}).', 'error')
                return redirect(url_for('assets_index'))
            
            asset = asset_response.json()
            print(f"✅ Asset loaded: {asset.get('Year', '')} {asset.get('Make', '')} {asset.get('Model', '')}")
            print(f"🔍 Asset details:")
            print(f"   - Asset ID: {asset.get('id')}")
            print(f"   - VIN: {asset.get('VIN', asset.get('Vin', 'N/A'))}")
            print(f"   - Account ID: {asset.get('account_id')}")
            print(f"   - Contact ID: {asset.get('contact_id')}")
            
            # Verify asset ID matches request
            if asset.get('id') != asset_id:
                print(f"❌ WARNING: Asset ID mismatch! Requested: {asset_id}, Received: {asset.get('id')}")
                flash(f'Asset ID mismatch. Please try again.', 'error')
                return redirect(url_for('assets_index'))
            
            # Initialize related data
            account = None
            contact = None
            loans = []
            cases = []
            
            # Load related account
            if asset.get('account_id'):
                try:
                    account_response = requests.get(
                        f"{fastapi_url}/api/accounts/{asset['account_id']}", 
                        headers=headers, 
                        timeout=10  # Increased timeout
                    )
                    if account_response.status_code == 200:
                        account = account_response.json()
                        print(f"✅ Account loaded: {account.get('account_name', 'Unknown')}")
                    else:
                        print(f"❌ Account load failed: {account_response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading account: {e}")
            
            # Load related contact
            if asset.get('contact_id'):
                try:
                    contact_response = requests.get(
                        f"{fastapi_url}/api/contacts/{asset['contact_id']}", 
                        headers=headers, 
                        timeout=10  # Increased timeout
                    )
                    if contact_response.status_code == 200:
                        contact = contact_response.json()
                        print(f"✅ Contact loaded")
                    else:
                        print(f"❌ Contact load failed: {contact_response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading contact: {e}")
            
            # IMPROVED LOANS MATCHING - FIXED API CALLS
            print(f"🔍 Starting comprehensive loan search...")
            
            # Strategy 1: Direct asset-to-loan relationship
            if asset.get('loan_id'):
                print(f"🔍 Trying direct loan_id: {asset.get('loan_id')}")
                try:
                    loan_response = requests.get(
                        f"{fastapi_url}/api/loans/{asset['loan_id']}", 
                        headers=headers, 
                        timeout=10
                    )
                    if loan_response.status_code == 200:
                        loans = [loan_response.json()]
                        print(f"✅ Found direct loan relationship: {len(loans)} loans")
                except Exception as e:
                    print(f"❌ Direct loan lookup failed: {e}")
            
            # Strategy 2: Account-based loan search - FIXED
            if not loans and asset.get('account_id'):
                print(f"🔍 Searching loans by account_id: {asset.get('account_id')}")
                
                # Use the main loans endpoint with parameters instead of trying different endpoints
                try:
                    print(f"🔍 Trying main endpoint: {fastapi_url}/api/loans/")
                    loan_response = requests.get(
                        f"{fastapi_url}/api/loans/",
                        headers=headers,
                        params={'account_id': asset['account_id']},
                        timeout=15
                    )
                    print(f"   Response: {loan_response.status_code}")
                    
                    if loan_response.status_code == 200:
                        loan_data = loan_response.json()
                        if isinstance(loan_data, dict):
                            loans = loan_data.get('items', [])
                        elif isinstance(loan_data, list):
                            loans = loan_data
                        
                        if loans:
                            print(f"✅ Found account-based loans: {len(loans)} loans")
                        else:
                            print(f"   Empty response from main endpoint")
                    elif loan_response.status_code == 401:
                        print(f"   ❌ 401 Unauthorized - checking session token")
                        # Try to refresh token or redirect to login
                        session.clear()
                        flash('Session expired. Please log in again.', 'error')
                        return redirect(url_for('auth.login'))
                    else:
                        print(f"   Failed: {loan_response.status_code} - {loan_response.text}")
                        
                except Exception as e:
                    print(f"   Exception: {e}")
            
            # Strategy 3: Vehicle matching (get all loans and match by vehicle details) - FIXED
            if not loans:
                print(f"🔍 Trying vehicle detail matching...")
                try:
                    all_loans_response = requests.get(
                        f"{fastapi_url}/api/loans/", 
                        headers=headers, 
                        timeout=20  # Increased timeout for all loans
                    )
                    print(f"   All loans response: {all_loans_response.status_code}")
                    
                    if all_loans_response.status_code == 200:
                        all_loans_data = all_loans_response.json()
                        all_loans = all_loans_data.get('items', all_loans_data) if isinstance(all_loans_data, dict) else all_loans_data
                        
                        print(f"   Total loans in system: {len(all_loans)}")
                        
                        # Get asset identifiers for matching
                        asset_vin = str(asset.get('VIN') or asset.get('Vin') or '').upper().strip()
                        asset_year = str(asset.get('Year') or '').strip()
                        asset_make = str(asset.get('Make') or '').upper().strip()
                        asset_model = str(asset.get('Model') or '').upper().strip()
                        asset_account_id = asset.get('account_id')
                        
                        print(f"   Asset matching criteria:")
                        print(f"     VIN: '{asset_vin}'")
                        print(f"     Year: '{asset_year}'")
                        print(f"     Make: '{asset_make}'")
                        print(f"     Model: '{asset_model}'")
                        print(f"     Account: {asset_account_id}")
                        
                        matched_loans = []
                        
                        for loan in all_loans:
                            match_score = 0
                            match_reasons = []
                            
                            # Method 1: VIN matching (highest priority)
                            loan_vin = str(loan.get('vehicle_vin') or loan.get('VIN') or '').upper().strip()
                            if asset_vin and loan_vin and asset_vin == loan_vin:
                                match_score += 10
                                match_reasons.append("VIN")
                            
                            # Method 2: Account + Vehicle details matching
                            if asset_account_id and loan.get('account_id') == asset_account_id:
                                match_score += 3
                                match_reasons.append("Account")
                                
                                # Check vehicle details
                                loan_year = str(loan.get('vehicle_year') or loan.get('Year') or '').strip()
                                loan_make = str(loan.get('vehicle_make') or loan.get('Make') or '').upper().strip()
                                loan_model = str(loan.get('vehicle_model') or loan.get('Model') or '').upper().strip()
                                
                                if asset_year and loan_year and asset_year == loan_year:
                                    match_score += 2
                                    match_reasons.append("Year")
                                
                                if asset_make and loan_make and asset_make == loan_make:
                                    match_score += 2
                                    match_reasons.append("Make")
                                
                                if asset_model and loan_model and asset_model == loan_model:
                                    match_score += 2
                                    match_reasons.append("Model")
                            
                            # Method 3: Contact matching
                            if asset.get('contact_id') and loan.get('contact_id') == asset.get('contact_id'):
                                match_score += 2
                                match_reasons.append("Contact")
                            
                            # Accept loans with match score >= 5 (VIN match or Account + 2 vehicle details)
                            if match_score >= 5:
                                matched_loans.append(loan)
                                print(f"   ✅ Matched loan {loan.get('contract_number', loan.get('id'))} (score: {match_score}, reasons: {', '.join(match_reasons)})")
                        
                        loans = matched_loans
                        print(f"✅ Vehicle matching found: {len(loans)} loans")
                    
                    elif all_loans_response.status_code == 401:
                        print(f"   ❌ 401 Unauthorized getting all loans - session expired")
                        session.clear()
                        flash('Session expired. Please log in again.', 'error')
                        return redirect(url_for('auth.login'))
                    else:
                        print(f"   Failed to get all loans: {all_loans_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Vehicle matching failed: {e}")
            
            # IMPROVED CASES MATCHING - FIXED API CALLS
            print(f"🔍 Starting comprehensive case search...")
            
            # Strategy 1: Direct loan-to-case relationship - FIXED
            if loans:
                loan_ids = [loan.get('id') for loan in loans if loan.get('id')]
                print(f"🔍 Searching cases by loan IDs: {loan_ids}")
                
                try:
                    all_cases_response = requests.get(
                        f"{fastapi_url}/api/cases/", 
                        headers=headers, 
                        timeout=20  # Increased timeout
                    )
                    print(f"   All cases response: {all_cases_response.status_code}")
                    
                    if all_cases_response.status_code == 200:
                        all_cases_data = all_cases_response.json()
                        all_cases = all_cases_data.get('items', all_cases_data) if isinstance(all_cases_data, dict) else all_cases_data
                        
                        print(f"   Total cases in system: {len(all_cases)}")
                        
                        matched_cases = []
                        for case in all_cases:
                            case_loan_id = case.get('loan_id')
                            case_account_id = case.get('account_id')
                            
                            # Match by loan ID
                            if case_loan_id in loan_ids:
                                matched_cases.append(case)
                                print(f"   ✅ Matched case {case.get('case_number', case.get('id'))} via loan {case_loan_id}")
                            
                            # Match by account ID as fallback
                            elif not matched_cases and asset.get('account_id') and case_account_id == asset.get('account_id'):
                                matched_cases.append(case)
                                print(f"   ✅ Matched case {case.get('case_number', case.get('id'))} via account {case_account_id}")
                        
                        cases = matched_cases
                        print(f"✅ Case matching found: {len(cases)} cases")
                    
                    elif all_cases_response.status_code == 401:
                        print(f"   ❌ 401 Unauthorized getting all cases - session expired")
                        session.clear()
                        flash('Session expired. Please log in again.', 'error')
                        return redirect(url_for('auth.login'))
                    else:
                        print(f"   Failed to get all cases: {all_cases_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Case matching failed: {e}")
            
            # Strategy 2: Account-based case search (if no loan matches) - FIXED
            elif asset.get('account_id'):
                print(f"🔍 Searching cases by account_id: {asset.get('account_id')}")
                
                # Use the main cases endpoint with parameters instead of trying different endpoints
                try:
                    print(f"🔍 Trying main endpoint: {fastapi_url}/api/cases/")
                    case_response = requests.get(
                        f"{fastapi_url}/api/cases/",
                        headers=headers,
                        params={'account_id': asset['account_id']},
                        timeout=15
                    )
                    print(f"   Response: {case_response.status_code}")
                    
                    if case_response.status_code == 200:
                        case_data = case_response.json()
                        if isinstance(case_data, dict):
                            cases = case_data.get('items', [])
                        elif isinstance(case_data, list):
                            cases = case_data
                        
                        if cases:
                            print(f"✅ Found account-based cases: {len(cases)} cases")
                        else:
                            print(f"   Empty response from main endpoint")
                    elif case_response.status_code == 401:
                        print(f"   ❌ 401 Unauthorized - session expired")
                        session.clear()
                        flash('Session expired. Please log in again.', 'error')
                        return redirect(url_for('auth.login'))
                    else:
                        print(f"   Failed: {case_response.status_code}")
                        
                except Exception as e:
                    print(f"   Exception: {e}")
            
            # Ensure data is properly formatted
            loans = loans or []
            cases = cases or []
            
            print(f"📊 Final data summary for asset {asset_id}:")
            print(f"   - Asset: {asset.get('Year', '')} {asset.get('Make', '')} {asset.get('Model', '')}")
            print(f"   - Account: {'Loaded' if account else 'None'}")
            print(f"   - Contact: {'Loaded' if contact else 'None'}")
            print(f"   - Loans: {len(loans)}")
            print(f"   - Cases: {len(cases)}")
            
            return render_template('assets/detail.html', 
                                asset=asset, 
                                account=account,
                                contact=contact,
                                loans=loans, 
                                cases=cases)
            
        except Exception as e:
            print(f"❌ Unexpected error for asset {asset_id}: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            flash(f'Unexpected error loading asset {asset_id}: {str(e)}', 'error')
            return redirect(url_for('assets_index'))

    @app.route('/assets/<int:asset_id>/edit')
    def assets_edit(asset_id):
        """Edit asset form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Fetch asset details
            response = requests.get(f"{fastapi_url}/api/assets/{asset_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Asset not found', 'error')
                return redirect(url_for('assets_index'))
            elif response.status_code != 200:
                flash('Error loading asset', 'error')
                return redirect(url_for('assets_index'))
            
            asset = response.json()
            
            # Load accounts for dropdown
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            
            accounts = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            return render_template('assets/form.html', asset=asset, accounts=accounts)
            
        except requests.RequestException as e:
            flash(f'Error loading asset: {str(e)}', 'error')
            return redirect(url_for('assets_index'))

    @app.route('/assets/<int:asset_id>/update', methods=['POST'])
    def assets_update(asset_id):
        """Update asset"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            asset_data = {
                'Year': int(request.form.get('Year')) if request.form.get('Year') else None,
                'Make': request.form.get('Make'),
                'Model': request.form.get('Model'),
                'VIN': request.form.get('VIN'),
                'mileage': int(request.form.get('mileage')) if request.form.get('mileage') else None,
                'color': request.form.get('color'),
                'status': request.form.get('status', 'Active'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None
            }
            
            # Add financial fields if provided
            financial_fields = ['value', 'purchase_price', 'loan_balance']
            for field in financial_fields:
                value = request.form.get(field)
                if value:
                    try:
                        asset_data[field] = float(value)
                    except ValueError:
                        pass
            
            # Add other fields
            other_fields = ['condition', 'location', 'license_plate', 'insurance_company', 'notes']
            for field in other_fields:
                value = request.form.get(field)
                if value:
                    asset_data[field] = value
            
            # Add date fields
            date_fields = ['purchase_date', 'registration_date', 'insurance_expiry']
            for field in date_fields:
                value = request.form.get(field)
                if value:
                    asset_data[field] = value
            
            # Remove None values
            asset_data = {k: v for k, v in asset_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.put(
                f"{fastapi_url}/api/assets/{asset_id}",
                headers=headers,
                json=asset_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Asset not found', 'error')
                return redirect(url_for('assets_index'))
            elif response.status_code == 200:
                flash('Asset updated successfully!', 'success')
                return redirect(url_for('assets_detail', asset_id=asset_id))
            else:
                flash('Error updating asset. Please try again.', 'error')
                return redirect(url_for('assets_edit', asset_id=asset_id))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('assets_edit', asset_id=asset_id))
        except requests.RequestException as e:
            flash(f'Error updating asset: {str(e)}', 'error')
            return redirect(url_for('assets_edit', asset_id=asset_id))

    @app.route('/assets/<int:asset_id>/delete', methods=['POST'])
    def assets_delete(asset_id):
        """Delete asset"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.delete(f"{fastapi_url}/api/assets/{asset_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Asset not found', 'error')
                return redirect(url_for('assets_index'))
            elif response.status_code == 200:
                flash('Asset deleted successfully!', 'success')
                return redirect(url_for('assets_index'))
            else:
                flash('Error deleting asset. Please try again.', 'error')
                return redirect(url_for('assets_detail', asset_id=asset_id))
            
        except requests.RequestException as e:
            flash(f'Error deleting asset: {str(e)}', 'error')
            return redirect(url_for('assets_detail', asset_id=asset_id))
        
    # Add this after your existing routes (around line 800+ in your app.py)
    # Place it before the namespace classes section

    @app.route('/test-assets-search')
    def test_assets_search():
        """Temporary route to test asset search functionality"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        search_term = request.args.get('search', '')
        
        try:
            access_token = session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Test 1: Get all assets without search
            print(f"🔍 TEST 1: Getting all assets")
            all_assets_response = requests.get(f"{fastapi_url}/api/assets/", headers=headers, timeout=10)
            
            if all_assets_response.status_code == 200:
                all_assets_data = all_assets_response.json()
                all_assets = all_assets_data.get('items', all_assets_data) if isinstance(all_assets_data, dict) else all_assets_data
                
                print(f"✅ Found {len(all_assets)} total assets")
                
                # Show VIN fields in first few assets
                for i, asset in enumerate(all_assets[:3]):
                    print(f"Asset {i+1}: ID={asset.get('id')}, VIN={asset.get('VIN')}, Vin={asset.get('Vin')}, vin={asset.get('vin')}")
            
            # Test 2: Search with the problematic VIN
            if search_term:
                print(f"🔍 TEST 2: Searching for '{search_term}'")
                
                # Try different search parameters
                search_tests = [
                    {'search': search_term},
                    {'VIN': search_term},
                    {'Vin': search_term},
                    {'vin': search_term.lower()},
                    {'q': search_term},  # Generic query parameter
                ]
                
                for i, params in enumerate(search_tests):
                    print(f"🔍 Search test {i+1}: {params}")
                    search_response = requests.get(f"{fastapi_url}/api/assets/", headers=headers, params=params, timeout=10)
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        search_results = search_data.get('items', search_data) if isinstance(search_data, dict) else search_data
                        print(f"✅ Found {len(search_results)} results with {params}")
                        
                        # Show matching assets
                        for result in search_results[:2]:
                            print(f"  Match: ID={result.get('id')}, VIN={result.get('VIN')}, Vehicle={result.get('Year')} {result.get('Make')} {result.get('Model')}")
                    else:
                        print(f"❌ Search failed with {params}: {search_response.status_code}")
            
            # Test 3: Client-side search simulation
            if search_term and all_assets:
                print(f"🔍 TEST 3: Client-side search simulation for '{search_term}'")
                search_lower = search_term.lower()
                
                client_matches = []
                for asset in all_assets:
                    # Check various fields
                    matches = [
                        str(asset.get('VIN', '')).lower(),
                        str(asset.get('Vin', '')).lower(), 
                        str(asset.get('vin', '')).lower(),
                        str(asset.get('Make', '')).lower(),
                        str(asset.get('Model', '')).lower(),
                        str(asset.get('Year', '')).lower()
                    ]
                    
                    if any(search_lower in match for match in matches):
                        client_matches.append(asset)
                
                print(f"✅ Client-side search found {len(client_matches)} matches")
                for match in client_matches[:3]:
                    print(f"  Match: ID={match.get('id')}, VIN={match.get('VIN')}, Vehicle={match.get('Year')} {match.get('Make')} {match.get('Model')}")
            
            # Return results as JSON for easy viewing
            result = {
                'search_term': search_term,
                'total_assets': len(all_assets) if 'all_assets' in locals() else 0,
                'sample_assets': all_assets[:3] if 'all_assets' in locals() else [],
                'tests_completed': True
            }
            
            if search_term and 'client_matches' in locals():
                result['client_search_results'] = len(client_matches)
                result['client_matches'] = client_matches[:3]
            
            return jsonify(result)
            
        except Exception as e:
            print(f"❌ Test error: {str(e)}")
            return jsonify({
                'error': str(e),
                'search_term': search_term,
                'tests_completed': False
            }), 500


    # Legacy assets route for backward compatibility
    @app.route('/assets_page')
    def assets_page():
        """Legacy redirect"""
        return redirect(url_for('assets_index'))

    # =============================================
    # CASES ROUTES
    # =============================================

    @app.route('/cases')
    def cases_index():
        """Main cases listing page with updated filters - defaults to 'New' status"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            # Get filter parameters - UPDATED to default status to 'New'
            search = request.args.get('search', '')
            # 🎯 KEY CHANGE: Default to 'New' status unless explicitly overridden
            status = request.args.get('status', 'New')
            priority = request.args.get('priority', '')
            case_type = request.args.get('type', '')
            financial_institution = request.args.get('financial_institution', '')
            page = int(request.args.get('page', 1))
            per_page = 20
            
            # 🔧 Special handling: If user explicitly selects "All Statuses", don't filter by status
            if request.args.get('status') == '':  # User explicitly chose "All Statuses"
                status = ''
            
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Build API query parameters - UPDATED to include financial_institution
            params = {
                'skip': (page - 1) * per_page,
                'limit': per_page
            }
            
            if search:
                params['search'] = search
            if status:  # Only add status filter if not empty
                params['status'] = status
            if priority:
                params['priority'] = priority
            if case_type:
                params['case_type'] = case_type
            if financial_institution:
                params['financial_institution'] = financial_institution
            
            print(f"🔍 Cases API call params: {params}")  # Debug logging
            
            # Fetch cases from FastAPI
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.get(
                f"{fastapi_url}/api/cases/",
                headers=headers,
                params=params,
                timeout=15  # Increased timeout
            )
            
            print(f"📡 FastAPI response status: {response.status_code}")  # Debug logging
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            
            if response.status_code != 200:
                print(f"❌ FastAPI error: {response.status_code} - {response.text}")
                flash('Error loading cases. Please try again.', 'error')
                return render_template('cases/index.html', 
                                    cases=[], 
                                    financial_institutions=[],
                                    search=search, 
                                    status=status, 
                                    priority=priority, 
                                    case_type=case_type,
                                    financial_institution=financial_institution,
                                    page=1, 
                                    total_pages=1, 
                                    total=0,
                                    has_prev=False,
                                    has_next=False)
            
            data = response.json()
            print(f"📊 Cases data received: {type(data)}")  # Debug logging
            
            # Handle both paginated and non-paginated responses
            if isinstance(data, dict) and 'items' in data:
                cases = data['items']
                total = data.get('total', len(cases))
            else:
                cases = data if isinstance(data, list) else []
                total = len(cases)
            
            print(f"✅ Cases loaded: {len(cases)} of {total} total")  # Debug logging
            
            # Fetch financial institutions for filter dropdown
            financial_institutions = []
            try:
                institutions_response = requests.get(
                    f"{fastapi_url}/api/cases/stats/financial-institutions",
                    headers=headers,
                    timeout=10
                )
                if institutions_response.status_code == 200:
                    institutions_data = institutions_response.json()
                    financial_institutions = institutions_data.get('financial_institutions', [])
                    print(f"✅ Financial institutions loaded: {len(financial_institutions)}")
                else:
                    print(f"⚠️ Could not load financial institutions: {institutions_response.status_code}")
            except Exception as e:
                print(f"❌ Error loading financial institutions: {e}")
                financial_institutions = []
            
            # Calculate pagination
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            has_prev = page > 1
            has_next = page < total_pages
            
            return render_template('cases/index.html',
                                cases=cases,
                                financial_institutions=financial_institutions,
                                search=search,
                                status=status,
                                priority=priority,
                                case_type=case_type,
                                financial_institution=financial_institution,
                                page=page,
                                total_pages=total_pages,
                                total=total,
                                has_prev=has_prev,
                                has_next=has_next)
            
        except requests.RequestException as e:
            print(f"❌ Request error: {str(e)}")
            flash(f'Error loading cases: {str(e)}', 'error')
            return render_template('cases/index.html', 
                                cases=[], 
                                financial_institutions=[],
                                search='', 
                                status='New',  # 🎯 Default to 'New' in error case too
                                priority='', 
                                case_type='',
                                financial_institution='',
                                page=1, 
                                total_pages=1, 
                                total=0,
                                has_prev=False,
                                has_next=False)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('cases/index.html', 
                                cases=[], 
                                financial_institutions=[],
                                search='', 
                                status='New',  # 🎯 Default to 'New' in error case too
                                priority='', 
                                case_type='',
                                financial_institution='',
                                page=1, 
                                total_pages=1, 
                                total=0,
                                has_prev=False,
                                has_next=False)

    @app.route('/cases/new')
    def cases_new():
        """New case form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Load accounts and contacts for dropdowns
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            contacts_response = requests.get(f"{fastapi_url}/api/contacts/", headers=headers)
            loans_response = requests.get(f"{fastapi_url}/api/loans/", headers=headers)
            
            accounts = []
            contacts = []
            loans = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                contacts = contacts_data.get('items', contacts_data) if isinstance(contacts_data, dict) else contacts_data
                
            if loans_response.status_code == 200:
                loans_data = loans_response.json()
                loans = loans_data.get('items', loans_data) if isinstance(loans_data, dict) else loans_data
            
            return render_template('cases/form.html', case=None, accounts=accounts, contacts=contacts, loans=loans)
            
        except requests.RequestException as e:
            flash(f'Error loading form data: {str(e)}', 'error')
            return render_template('cases/form.html', case=None, accounts=[], contacts=[], loans=[])

    @app.route('/cases/create', methods=['POST'])
    def cases_create():
        """Create new case"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            case_data = {
                'subject': request.form.get('subject'),
                'description': request.form.get('description'),
                'case_type': request.form.get('case_type'),
                'priority': request.form.get('priority', 'Low'),
                'status': request.form.get('status', 'Open'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
                'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None,
                'loan_id': int(request.form.get('loan_id')) if request.form.get('loan_id') else None,
                'assigned_team': request.form.get('assigned_team'),
                'due_date': request.form.get('due_date'),
                'category': request.form.get('category')
            }
            
            # Remove None values
            case_data = {k: v for k, v in case_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.post(
                f"{fastapi_url}/api/cases/",
                headers=headers,
                json=case_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            
            if response.status_code in [200, 201]:
                flash('Case created successfully!', 'success')
                return redirect(url_for('cases_index'))
            else:
                flash('Error creating case. Please try again.', 'error')
                return redirect(url_for('cases_new'))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('cases_new'))
        except requests.RequestException as e:
            flash(f'Error creating case: {str(e)}', 'error')
            return redirect(url_for('cases_new'))

    @app.route('/cases/<int:case_id>')
    def cases_detail(case_id):
        """Case detail view with comprehensive related data loading"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            print(f"🔍 Loading case details for ID: {case_id}")
            
            # Fetch case details with relationships
            response = requests.get(f"{fastapi_url}/api/cases/{case_id}", headers=headers, timeout=15)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Case not found', 'error')
                return redirect(url_for('cases_index'))
            elif response.status_code != 200:
                print(f"❌ Case API error: {response.status_code} - {response.text}")
                flash('Error loading case details', 'error')
                return redirect(url_for('cases_index'))
            
            case = response.json()
            print(f"✅ Case loaded: {case.get('case_number', case.get('id'))} - {case.get('subject', 'No subject')}")
            print(f"🔍 Case relationships: account_id={case.get('account_id')}, contact_id={case.get('contact_id')}, loan_id={case.get('loan_id')}")
            
            # Initialize related data
            account = None
            contact = None
            loan = None
            assets = []
            
            # Load related account
            if case.get('account_id'):
                try:
                    print(f"🔍 Loading account ID: {case.get('account_id')}")
                    account_response = requests.get(
                        f"{fastapi_url}/api/accounts/{case['account_id']}", 
                        headers=headers, 
                        timeout=10
                    )
                    if account_response.status_code == 200:
                        account = account_response.json()
                        print(f"✅ Account loaded: {account.get('account_name', 'Unknown')}")
                    else:
                        print(f"❌ Account load failed: {account_response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading account: {e}")
            
            # Load related contact
            if case.get('contact_id'):
                try:
                    print(f"🔍 Loading contact ID: {case.get('contact_id')}")
                    contact_response = requests.get(
                        f"{fastapi_url}/api/contacts/{case['contact_id']}", 
                        headers=headers, 
                        timeout=10
                    )
                    if contact_response.status_code == 200:
                        contact = contact_response.json()
                        print(f"✅ Contact loaded: {contact.get('display_name', contact.get('first_name', '') + ' ' + contact.get('last_name', ''))}")
                    else:
                        print(f"❌ Contact load failed: {contact_response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading contact: {e}")
            
            # Load related loan
            if case.get('loan_id'):
                try:
                    print(f"🔍 Loading loan ID: {case.get('loan_id')}")
                    loan_response = requests.get(
                        f"{fastapi_url}/api/loans/{case['loan_id']}", 
                        headers=headers, 
                        timeout=10
                    )
                    if loan_response.status_code == 200:
                        loan = loan_response.json()
                        print(f"✅ Loan loaded: Contract #{loan.get('contract_number', loan.get('contractnumber', 'Unknown'))}")
                    else:
                        print(f"❌ Loan load failed: {loan_response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading loan: {e}")
            
            # Load related assets - try multiple approaches
            print(f"🔍 Loading assets...")
            
            # Strategy 1: Direct loan-to-asset relationship
            if loan and loan.get('id'):
                try:
                    print(f"🔍 Searching assets by loan ID: {loan.get('id')}")
                    assets_response = requests.get(
                        f"{fastapi_url}/api/assets/",
                        headers=headers,
                        params={'loan_id': loan['id']},
                        timeout=10
                    )
                    if assets_response.status_code == 200:
                        assets_data = assets_response.json()
                        if isinstance(assets_data, dict):
                            assets = assets_data.get('items', [])
                        elif isinstance(assets_data, list):
                            assets = assets_data
                        
                        if assets:
                            print(f"✅ Found {len(assets)} assets via loan relationship")
                except Exception as e:
                    print(f"❌ Error loading assets by loan: {e}")
            
            # Strategy 2: Account-based asset search
            if not assets and case.get('account_id'):
                try:
                    print(f"🔍 Searching assets by account ID: {case.get('account_id')}")
                    assets_response = requests.get(
                        f"{fastapi_url}/api/assets/",
                        headers=headers,
                        params={'account_id': case['account_id']},
                        timeout=10
                    )
                    if assets_response.status_code == 200:
                        assets_data = assets_response.json()
                        if isinstance(assets_data, dict):
                            assets = assets_data.get('items', [])
                        elif isinstance(assets_data, list):
                            assets = assets_data
                        
                        if assets:
                            print(f"✅ Found {len(assets)} assets via account relationship")
                except Exception as e:
                    print(f"❌ Error loading assets by account: {e}")
            
            # Strategy 3: Get all assets and filter by related data
            if not assets and (loan or account):
                try:
                    print(f"🔍 Searching all assets for matches...")
                    all_assets_response = requests.get(
                        f"{fastapi_url}/api/assets/", 
                        headers=headers, 
                        timeout=15
                    )
                    if all_assets_response.status_code == 200:
                        all_assets_data = all_assets_response.json()
                        all_assets = all_assets_data.get('items', all_assets_data) if isinstance(all_assets_data, dict) else all_assets_data
                        
                        matched_assets = []
                        for asset in all_assets:
                            # Match by account ID
                            if case.get('account_id') and asset.get('account_id') == case.get('account_id'):
                                matched_assets.append(asset)
                            # Match by loan ID
                            elif loan and asset.get('loan_id') == loan.get('id'):
                                matched_assets.append(asset)
                        
                        assets = matched_assets
                        if assets:
                            print(f"✅ Found {len(assets)} assets via comprehensive search")
                except Exception as e:
                    print(f"❌ Error in comprehensive asset search: {e}")
            
            # Fallback: If no account/contact/loan found via case relationships, try to infer from loan data
            if not account and not contact and loan:
                print(f"🔍 Trying to load related data from loan...")
                
                # Try to get account from loan
                if loan.get('account_id') and not account:
                    try:
                        loan_account_response = requests.get(
                            f"{fastapi_url}/api/accounts/{loan['account_id']}", 
                            headers=headers, 
                            timeout=10
                        )
                        if loan_account_response.status_code == 200:
                            account = loan_account_response.json()
                            print(f"✅ Account loaded via loan: {account.get('account_name', 'Unknown')}")
                    except Exception as e:
                        print(f"❌ Error loading account via loan: {e}")
                
                # Try to get contact from loan
                contact_id = loan.get('primary_contact') or loan.get('contact_id')
                if contact_id and not contact:
                    try:
                        loan_contact_response = requests.get(
                            f"{fastapi_url}/api/contacts/{contact_id}", 
                            headers=headers, 
                            timeout=10
                        )
                        if loan_contact_response.status_code == 200:
                            contact = loan_contact_response.json()
                            print(f"✅ Contact loaded via loan: {contact.get('display_name', 'Unknown')}")
                    except Exception as e:
                        print(f"❌ Error loading contact via loan: {e}")
            
            # Ensure assets is always a list
            if not isinstance(assets, list):
                assets = []
            
            print(f"📊 Final data summary for case {case_id}:")
            print(f"   - Case: {case.get('case_number', case.get('id'))} - {case.get('subject', 'No subject')}")
            print(f"   - Account: {'✅ Loaded' if account else '❌ None'}")
            print(f"   - Contact: {'✅ Loaded' if contact else '❌ None'}")
            print(f"   - Loan: {'✅ Loaded' if loan else '❌ None'}")
            print(f"   - Assets: {len(assets)} found")
            
            return render_template('cases/detail.html', 
                                case=case, 
                                account=account, 
                                contact=contact, 
                                loan=loan,
                                assets=assets)
            
        except requests.RequestException as e:
            print(f"❌ Request error: {str(e)}")
            flash(f'Error loading case: {str(e)}', 'error')
            return redirect(url_for('cases_index'))
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            flash('An unexpected error occurred while loading case details.', 'error')
            return redirect(url_for('cases_index'))

    @app.route('/cases/<int:case_id>/edit')
    def cases_edit(case_id):
        """Edit case form"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            
            # Fetch case details
            response = requests.get(f"{fastapi_url}/api/cases/{case_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Case not found', 'error')
                return redirect(url_for('cases_index'))
            elif response.status_code != 200:
                flash('Error loading case', 'error')
                return redirect(url_for('cases_index'))
            
            case = response.json()
            
            # Load accounts, contacts, and loans for dropdowns
            accounts_response = requests.get(f"{fastapi_url}/api/accounts/", headers=headers)
            contacts_response = requests.get(f"{fastapi_url}/api/contacts/", headers=headers)
            loans_response = requests.get(f"{fastapi_url}/api/loans/", headers=headers)
            
            accounts = []
            contacts = []
            loans = []
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                accounts = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
            
            if contacts_response.status_code == 200:
                contacts_data = contacts_response.json()
                contacts = contacts_data.get('items', contacts_data) if isinstance(contacts_data, dict) else contacts_data
                
            if loans_response.status_code == 200:
                loans_data = loans_response.json()
                loans = loans_data.get('items', loans_data) if isinstance(loans_data, dict) else loans_data
            
            return render_template('cases/form.html', case=case, accounts=accounts, contacts=contacts, loans=loans)
            
        except requests.RequestException as e:
            flash(f'Error loading case: {str(e)}', 'error')
            return redirect(url_for('cases_index'))

    @app.route('/cases/<int:case_id>/update', methods=['POST'])
    def cases_update(case_id):
        """Update case"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            # Get form data
            case_data = {
                'subject': request.form.get('subject'),
                'description': request.form.get('description'),
                'case_type': request.form.get('case_type'),
                'priority': request.form.get('priority', 'Low'),
                'status': request.form.get('status', 'Open'),
                'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
                'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None,
                'loan_id': int(request.form.get('loan_id')) if request.form.get('loan_id') else None,
                'assigned_team': request.form.get('assigned_team'),
                'due_date': request.form.get('due_date'),
                'category': request.form.get('category'),
                'resolution': request.form.get('resolution'),
                'internal_notes': request.form.get('internal_notes')
            }
            
            # Remove None values
            case_data = {k: v for k, v in case_data.items() if v is not None and v != ''}
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.put(
                f"{fastapi_url}/api/cases/{case_id}",
                headers=headers,
                json=case_data,
                timeout=10
            )
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Case not found', 'error')
                return redirect(url_for('cases_index'))
            elif response.status_code == 200:
                flash('Case updated successfully!', 'success')
                return redirect(url_for('cases_detail', case_id=case_id))
            else:
                flash('Error updating case. Please try again.', 'error')
                return redirect(url_for('cases_edit', case_id=case_id))
            
        except (ValueError, TypeError) as e:
            flash(f'Invalid form data: {str(e)}', 'error')
            return redirect(url_for('cases_edit', case_id=case_id))
        except requests.RequestException as e:
            flash(f'Error updating case: {str(e)}', 'error')
            return redirect(url_for('cases_edit', case_id=case_id))

    @app.route('/cases/<int:case_id>/delete', methods=['POST'])
    def cases_delete(case_id):
        """Delete case"""
        auth_check = require_auth()
        if auth_check:
            return auth_check
        
        try:
            headers = get_auth_headers()
            if not headers:
                return redirect(url_for('auth.login'))
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            response = requests.delete(f"{fastapi_url}/api/cases/{case_id}", headers=headers)
            
            if response.status_code == 401:
                session.clear()
                return redirect(url_for('auth.login'))
            elif response.status_code == 404:
                flash('Case not found', 'error')
                return redirect(url_for('cases_index'))
            elif response.status_code == 200:
                flash('Case deleted successfully!', 'success')
                return redirect(url_for('cases_index'))
            else:
                flash('Error deleting case. Please try again.', 'error')
                return redirect(url_for('cases_detail', case_id=case_id))
            
        except requests.RequestException as e:
            flash(f'Error deleting case: {str(e)}', 'error')
            return redirect(url_for('cases_detail', case_id=case_id))
        
    @app.route('/debug-filters-main')
    def debug_filters_main():
        """Main debug route to test filter API directly"""
        try:
            access_token = session.get('access_token')
            if not access_token:
                return "❌ Not logged in", 401
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            fastapi_url = app.config['FASTAPI_BASE_URL']
            print(f"🔍 Testing: {fastapi_url}/api/cases/filters")
            
            response = requests.get(
                f"{fastapi_url}/api/cases/filters",
                headers=headers,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    result = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Filter API Debug</title>
                        <style>
                            body {{ font-family: monospace; padding: 20px; }}
                            .success {{ color: green; }}
                            .error {{ color: red; }}
                            pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
                            ul {{ margin: 10px 0; }}
                            li {{ margin: 5px 0; }}
                        </style>
                    </head>
                    <body>
                        <h1 class="success">✅ Filter API Working!</h1>
                        <p><strong>Status:</strong> {response.status_code}</p>
                        <p><strong>FastAPI URL:</strong> {fastapi_url}/api/cases/filters</p>
                        <p><strong>Generated at:</strong> {data.get('generated_at', 'Unknown')}</p>
                        
                        <h2>Raw Response:</h2>
                        <pre>{response.text}</pre>
                        
                        <h2>Parsed Filters:</h2>
                    """
                    
                    filters = data.get('filters', {})
                    if filters:
                        for category, options in filters.items():
                            result += f"<h3>{category} ({len(options)} options):</h3><ul>"
                            for option in options[:10]:  # Show first 10 options
                                result += f"<li>{option}</li>"
                            if len(options) > 10:
                                result += f"<li>... and {len(options) - 10} more</li>"
                            result += "</ul>"
                    else:
                        result += "<p class='error'>❌ No filters found in response</p>"
                    
                    error_msg = data.get('error', '')
                    if error_msg:
                        result += f"<h3 class='error'>API Error:</h3><p>{error_msg}</p>"
                    
                    result += """
                        <h2>Next Steps:</h2>
                        <ul>
                            <li><a href="/cases">Test on Cases Page</a></li>
                            <li><a href="/cases/debug-filters">Test via Blueprint Route</a></li>
                            <li><a href="/">Back to Dashboard</a></li>
                        </ul>
                    </body>
                    </html>
                    """
                    
                    return result
                    
                except Exception as json_error:
                    return f"""
                    <h1 class="error">❌ JSON Parse Error</h1>
                    <p><strong>Status:</strong> {response.status_code}</p>
                    <p><strong>JSON Error:</strong> {json_error}</p>
                    <p><strong>Raw Response:</strong></p>
                    <pre>{response.text}</pre>
                    """
            else:
                return f"""
                <h1 class="error">❌ API Error</h1>
                <p><strong>Status:</strong> {response.status_code}</p>
                <p><strong>URL:</strong> {fastapi_url}/api/cases/filters</p>
                <p><strong>Response:</strong></p>
                <pre>{response.text}</pre>
                <p><a href="/">← Back to Dashboard</a></p>
                """
        
        except Exception as e:
            import traceback
            return f"""
            <h1 class="error">❌ Exception</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback.format_exc()}</pre>
            <p><a href="/">← Back to Dashboard</a></p>
            """

    # Legacy cases route for backward compatibility
    @app.route('/cases_page')
    def cases_page():
        """Legacy redirect"""
        return redirect(url_for('cases_index'))
    
    # =============================================
    # ADMIN DEBUG ROUTES - ADD HERE
    # =============================================
    
    @app.route('/debug-admin')
    def debug_admin():
        """Comprehensive admin debugging route"""
        
        debug_info = {
            'session_data': dict(session),
            'user_info': session.get('user_info', {}),
            'has_access_token': 'access_token' in session,
            'current_user': session.get('user_info', {}).get('username', 'None'),
            'is_admin_in_session': session.get('user_info', {}).get('is_admin', False),
            'user_roles': session.get('user_info', {}).get('user_roles', []),
            'request_endpoint': request.endpoint,
            'request_path': request.path
        }
        
        # Try to check admin access via your auth utils
        try:
            from utils.auth import is_admin, get_user_roles, check_admin_access
            debug_info['auth_utils_is_admin'] = is_admin()
            debug_info['auth_utils_roles'] = get_user_roles()
            
            if 'access_token' in session:
                admin_check = check_admin_access(session['access_token'])
                debug_info['admin_check_result'] = admin_check
        except Exception as e:
            debug_info['auth_utils_error'] = str(e)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Debug</title>
            <style>
                body {{ font-family: monospace; padding: 20px; }}
                .debug-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ccc; }}
                .admin-granted {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .admin-denied {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                pre {{ background: #f8f9fa; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>Admin Debug Information</h1>
            
            <div class="debug-section">
                <h2>Current Status</h2>
                <p><strong>Admin Access:</strong> {'✅ GRANTED' if debug_info.get('is_admin_in_session') else '❌ DENIED'}</p>
                <p><strong>Current User:</strong> {debug_info['current_user']}</p>
            </div>
            
            <div class="debug-section">
                <h2>Session Data</h2>
                <pre>{debug_info}</pre>
            </div>
            
            <div class="debug-section admin-granted">
                <h2>🔧 Manual Admin Grant</h2>
                <button onclick="grantAdmin()">Grant Admin Access</button>
                <button onclick="checkMenuVisibility()">Check Menu Visibility</button>
                <button onclick="forceShowMenu()">Force Show Admin Menu</button>
            </div>
            
            <div class="debug-section">
                <h2>🔍 Menu Item Status</h2>
                <div id="menuStatus">Checking...</div>
            </div>
            
            <script>
                function grantAdmin() {{
                    fetch('/grant-admin-access', {{
                        method: 'POST',
                        credentials: 'same-origin'
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert('Admin access granted: ' + JSON.stringify(data));
                        location.reload();
                    }})
                    .catch(error => {{
                        alert('Error: ' + error);
                    }});
                }}
                
                function checkMenuVisibility() {{
                    const adminMenuItem = document.querySelector('#adminMenuItem');
                    const status = document.getElementById('menuStatus');
                    
                    if (adminMenuItem) {{
                        status.innerHTML = `
                            <p><strong>Admin Menu Item Found:</strong> ✅</p>
                            <p><strong>Display:</strong> ${{adminMenuItem.style.display || 'default'}}</p>
                            <p><strong>Visibility:</strong> ${{adminMenuItem.style.visibility || 'default'}}</p>
                            <p><strong>Classes:</strong> ${{adminMenuItem.className}}</p>
                            <p><strong>Hidden:</strong> ${{adminMenuItem.hidden}}</p>
                            <p><strong>Computed Display:</strong> ${{window.getComputedStyle(adminMenuItem).display}}</p>
                        `;
                    }} else {{
                        status.innerHTML = '<p><strong>Admin Menu Item:</strong> ❌ NOT FOUND</p>';
                    }}
                    
                    // Check localStorage
                    const adminConfirmed = localStorage.getItem('admin_access_confirmed');
                    const userInfo = localStorage.getItem('user_info');
                    status.innerHTML += `
                        <p><strong>LocalStorage Admin:</strong> ${{adminConfirmed || 'null'}}</p>
                        <p><strong>LocalStorage User Info:</strong> ${{userInfo || 'null'}}</p>
                    `;
                }}
                
                function forceShowMenu() {{
                    const adminMenuItem = document.querySelector('#adminMenuItem');
                    if (adminMenuItem) {{
                        adminMenuItem.style.display = 'block';
                        adminMenuItem.style.visibility = 'visible';
                        adminMenuItem.classList.remove('hidden');
                        localStorage.setItem('admin_access_confirmed', 'true');
                        alert('Admin menu forced to show!');
                    }} else {{
                        alert('Admin menu item not found in DOM!');
                    }}
                }}
                
                // Auto-check on load
                setTimeout(checkMenuVisibility, 500);
            </script>
            
            <p><a href="/">← Back to Dashboard</a></p>
        </body>
        </html>
        """

    @app.route('/grant-admin-access', methods=['POST'])
    def grant_admin_access():
        """Grant admin access to current user"""
        if 'user_info' not in session:
            return {'error': 'Not logged in'}, 401
        
        # Force admin access
        session['user_info']['is_admin'] = True
        session['user_info']['user_roles'] = ['admin']
        session.permanent = True
        
        return {
            'success': True,
            'message': 'Admin access granted',
            'user_info': session['user_info']
        }

    # =============================================
    # API PROXY ROUTES
    # =============================================
    
    @app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def api_proxy(path):
        """Proxy API requests to FastAPI backend"""
        auth_check = require_auth()
        if auth_check:
            return jsonify({'error': 'Authentication required'}), 401
        
        headers = get_auth_headers()
        if not headers:
            return jsonify({'error': 'No authorization token'}), 401
        
        try:
            # Forward the request to FastAPI
            fastapi_url = app.config['FASTAPI_BASE_URL']
            url = f"{fastapi_url}/api/{path}"
            
            if request.method == 'GET':
                response = requests.get(url, headers=headers, params=request.args)
            elif request.method == 'POST':
                response = requests.post(url, headers=headers, json=request.get_json())
            elif request.method == 'PUT':
                response = requests.put(url, headers=headers, json=request.get_json())
            elif request.method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return jsonify(response.json()), response.status_code
            
        except requests.RequestException as e:
            return jsonify({'error': str(e)}), 500

    # =============================================
    # LEGACY ROUTES AND OTHER SECTIONS
    # =============================================

    # Legacy route aliases for backwards compatibility
    @app.route('/accounts_page')
    def accounts_page():
        """Legacy redirect"""
        return redirect(url_for('accounts_index'))
    
    # Add these improved template filters to your app.py

    @app.template_filter('safe_currency')
    def safe_currency_filter(value):
        """Format value as currency with null safety"""
        try:
            if value is None or value == '':
                return "$0.00"
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @app.template_filter('safe_date')
    def safe_date_filter(value, format='%Y-%m-%d'):
        """Format a date value with null safety"""
        if value is None or value == '':
            return 'N/A'
        
        # Handle different input types
        if isinstance(value, str):
            try:
                # Try parsing ISO format first
                if 'T' in value:
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    elif '+' in value or value.count('-') > 2:
                        pass
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return 'N/A'
        
        if isinstance(value, datetime):
            return value.strftime(format)
        
        return str(value) if value else 'N/A'

    @app.template_filter('safe_string')
    def safe_string_filter(value, default='N/A'):
        """Return a safe string value with default fallback"""
        if value is None or value == '':
            return default
        return str(value)

    @app.template_filter('safe_number')
    def safe_number_filter(value, default=0):
        """Return a safe number value with default fallback"""
        try:
            if value is None or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    @app.template_filter('safe_int')
    def safe_int_filter(value, default=0):
        """Return a safe integer value with default fallback"""
        try:
            if value is None or value == '':
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default

    # =============================================
    # NAMESPACE CLASSES FOR BLUEPRINT-STYLE URLS
    # =============================================
    
    # Create namespace classes to make url_for('accounts.index') work
    class AccountsNamespace:
        @staticmethod
        def index():
            return url_for('accounts_index')
        
        @staticmethod 
        def new():
            return url_for('accounts_new')
            
        @staticmethod
        def create():
            return url_for('accounts_create')
            
        @staticmethod
        def detail(account_id):
            return url_for('accounts_detail', account_id=account_id)
            
        @staticmethod
        def edit(account_id):
            return url_for('accounts_edit', account_id=account_id)
            
        @staticmethod
        def update(account_id):
            return url_for('accounts_update', account_id=account_id)

    class ContactsNamespace:
        @staticmethod
        def index():
            return url_for('contacts_index')
        
        @staticmethod 
        def new():
            return url_for('contacts_new')
            
        @staticmethod
        def create():
            return url_for('contacts_create')
            
        @staticmethod
        def detail(contact_id):
            return url_for('contacts_detail', contact_id=contact_id)
            
        @staticmethod
        def edit(contact_id):
            return url_for('contacts_edit', contact_id=contact_id)
            
        @staticmethod
        def update(contact_id):
            return url_for('contacts_update', contact_id=contact_id)

    class LoansNamespace:
        @staticmethod
        def index():
            return url_for('loans_index')
        
        @staticmethod 
        def new():
            return url_for('loans_new')
            
        @staticmethod
        def create():
            return url_for('loans_create')
            
        @staticmethod
        def detail(loan_id):
            return url_for('loans_detail', loan_id=loan_id)
            
        @staticmethod
        def edit(loan_id):
            return url_for('loans_edit', loan_id=loan_id)
            
        @staticmethod
        def update(loan_id):
            return url_for('loans_update', loan_id=loan_id)
            
        @staticmethod
        def delete(loan_id):
            return url_for('loans_delete', loan_id=loan_id)


    class AssetsNamespace:
        @staticmethod
        def index():
            return url_for('assets_index')
        
        @staticmethod 
        def new():
            return url_for('assets_new')
            
        @staticmethod
        def create():
            return url_for('assets_create')
            
        @staticmethod
        def detail(asset_id):
            return url_for('assets_detail', asset_id=asset_id)
            
        @staticmethod
        def edit(asset_id):
            return url_for('assets_edit', asset_id=asset_id)
            
        @staticmethod
        def update(asset_id):
            return url_for('assets_update', asset_id=asset_id)
            
        @staticmethod
        def delete(asset_id):
            return url_for('assets_delete', asset_id=asset_id)

    class CasesNamespace:
        @staticmethod
        def index():
            return url_for('cases_index')
        
        @staticmethod 
        def new():
            return url_for('cases_new')
            
        @staticmethod
        def create():
            return url_for('cases_create')
            
        @staticmethod
        def detail(case_id):
            return url_for('cases_detail', case_id=case_id)
            
        @staticmethod
        def edit(case_id):
            return url_for('cases_edit', case_id=case_id)
            
        @staticmethod
        def update(case_id):
            return url_for('cases_update', case_id=case_id)
            
        @staticmethod
        def delete(case_id):
            return url_for('cases_delete', case_id=case_id)
    
    # Add the namespaces to Jinja2 globals so templates can access them
    # Replace the inject_namespaces function in your app.py with this:

    @app.context_processor
    def inject_namespaces():
        return dict(
            accounts_ns=AccountsNamespace(),
            contacts_ns=ContactsNamespace(),
            loans_ns=LoansNamespace(),
            assets_ns=AssetsNamespace(),
            cases_ns=CasesNamespace()
        )
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)