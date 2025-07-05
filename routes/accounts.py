# routes/accounts.py - Complete with enhanced cases debugging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
import traceback

# Create blueprint WITHOUT url_prefix since we're adding it during registration
accounts_bp = Blueprint('accounts', __name__)

def require_auth():
    """Helper function for authentication check"""
    if 'user_info' not in session:
        return redirect(url_for('auth.login'))
    return None

@accounts_bp.route('/')
def index():
    """Main accounts listing page"""
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
        from flask import current_app
        fastapi_url = current_app.config['FASTAPI_BASE_URL']
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
            
            # Handle case where API returns list directly
            if isinstance(data, list):
                accounts = data
                total = len(data)
            
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
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('accounts/index.html', accounts=[], search=search, account_type=account_type, status=status)

@accounts_bp.route('/new')
def new():
    """Route for creating new accounts"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    return render_template('accounts/new.html')

@accounts_bp.route('/create', methods=['POST'])
def create():
    """Route for handling account creation"""
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
        from flask import current_app
        fastapi_url = current_app.config['FASTAPI_BASE_URL']
        response = requests.post(
            f"{fastapi_url}/api/accounts/",
            headers=headers,
            json=account_data,
            timeout=10
        )
        
        if response.status_code == 201:
            flash('Account created successfully!', 'success')
            return redirect(url_for('accounts.index'))
        else:
            flash('Error creating account. Please try again.', 'error')
            return render_template('accounts/new.html', **account_data)
    
    except Exception as e:
        print(f"Error creating account: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('accounts/new.html')

@accounts_bp.route('/<int:account_id>')
def detail(account_id):
    """Route for viewing account details with enhanced cases support and debugging"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        access_token = session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        from flask import current_app
        fastapi_url = current_app.config['FASTAPI_BASE_URL']
        
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
            return redirect(url_for('accounts.index'))
        
        account = account_response.json()
        print(f"✅ Account loaded: {account.get('account_name', 'Unknown')}")
        print(f"🔍 Account data keys: {list(account.keys())}")
        
        # Initialize related data
        contacts = []
        loans = []
        assets = []
        cases = []
        
        # Try to load contacts with detailed error handling
        contact_endpoints = [
            f"/api/contacts/?account_id={account_id}",
            f"/api/contacts?account_id={account_id}",
            f"/api/accounts/{account_id}/contacts",
            f"/api/contacts/by-account/{account_id}"
        ]
        
        print(f"🔍 Loading contacts for account {account_id}...")
        for endpoint in contact_endpoints:
            try:
                contact_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                if contact_response.status_code == 200:
                    contact_data = contact_response.json()
                    contacts = contact_data.get('items', contact_data) if isinstance(contact_data, dict) else contact_data
                    print(f"✅ Contacts loaded from {endpoint}: {len(contacts)} contacts")
                    if contacts:
                        print(f"🔍 First contact keys: {list(contacts[0].keys()) if len(contacts) > 0 else 'No contacts'}")
                    break
                else:
                    print(f"❌ Contact endpoint {endpoint} failed: {contact_response.status_code}")
            except Exception as e:
                print(f"❌ Contact endpoint {endpoint} exception: {str(e)}")
                continue
        
        # Try to load loans with detailed error handling
        loan_endpoints = [
            f"/api/loans/?account_id={account_id}",
            f"/api/loans?account_id={account_id}",
            f"/api/accounts/{account_id}/loans",
            f"/api/loans/by-account/{account_id}"
        ]
        
        print(f"🔍 Loading loans for account {account_id}...")
        for endpoint in loan_endpoints:
            try:
                loan_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                if loan_response.status_code == 200:
                    loan_data = loan_response.json()
                    loans = loan_data.get('items', loan_data) if isinstance(loan_data, dict) else loan_data
                    print(f"✅ Loans loaded from {endpoint}: {len(loans)} loans")
                    if loans:
                        print(f"🔍 First loan keys: {list(loans[0].keys()) if len(loans) > 0 else 'No loans'}")
                    break
                else:
                    print(f"❌ Loan endpoint {endpoint} failed: {loan_response.status_code}")
            except Exception as e:
                print(f"❌ Loan endpoint {endpoint} exception: {str(e)}")
                continue
        
        # Try to load assets with detailed error handling
        asset_endpoints = [
            f"/api/assets/?account_id={account_id}",
            f"/api/assets?account_id={account_id}",
            f"/api/accounts/{account_id}/assets",
            f"/api/assets/by-account/{account_id}"
        ]
        
        print(f"🔍 Loading assets for account {account_id}...")
        for endpoint in asset_endpoints:
            try:
                asset_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=5)
                if asset_response.status_code == 200:
                    asset_data = asset_response.json()
                    assets = asset_data.get('items', asset_data) if isinstance(asset_data, dict) else asset_data
                    print(f"✅ Assets loaded from {endpoint}: {len(assets)} assets")
                    if assets:
                        print(f"🔍 First asset keys: {list(assets[0].keys()) if len(assets) > 0 else 'No assets'}")
                    break
                else:
                    print(f"❌ Asset endpoint {endpoint} failed: {asset_response.status_code}")
            except Exception as e:
                print(f"❌ Asset endpoint {endpoint} exception: {str(e)}")
                continue

        # ENHANCED CASES LOADING WITH EXTENSIVE DEBUGGING
        case_endpoints = [
            f"/api/cases/?account_id={account_id}",
            f"/api/cases?account_id={account_id}",
            f"/api/cases/",  # Get all cases to see what's available
            f"/api/cases/68",  # Try direct case ID if we know it exists
            f"/api/cases/by-account/{account_id}",
            f"/api/accounts/{account_id}/cases",
        ]

        print(f"🔍 DEBUG: Starting enhanced cases loading for account {account_id}")
        print(f"🔍 DEBUG: Using FastAPI URL: {fastapi_url}")
        print(f"🔍 DEBUG: Headers: {dict(headers)}")

        cases_found = False
        debug_info = []

        # First, let's try to get ALL cases to see what's in the system
        print(f"🔍 DEBUG: First, let's see ALL cases in the system...")
        try:
            all_cases_response = requests.get(f"{fastapi_url}/api/cases/", headers=headers, timeout=10)
            print(f"🔍 DEBUG: All cases endpoint status: {all_cases_response.status_code}")
            
            if all_cases_response.status_code == 200:
                all_cases_data = all_cases_response.json()
                print(f"🔍 DEBUG: All cases response type: {type(all_cases_data)}")
                print(f"🔍 DEBUG: All cases response keys: {list(all_cases_data.keys()) if isinstance(all_cases_data, dict) else 'Not a dict'}")
                
                # Handle different response formats
                if isinstance(all_cases_data, list):
                    all_cases = all_cases_data
                elif isinstance(all_cases_data, dict):
                    all_cases = all_cases_data.get('items', all_cases_data.get('data', []))
                else:
                    all_cases = []
                
                print(f"🔍 DEBUG: Total cases found in system: {len(all_cases)}")
                
                if all_cases:
                    print(f"🔍 DEBUG: First case structure: {all_cases[0]}")
                    print(f"🔍 DEBUG: First case keys: {list(all_cases[0].keys()) if isinstance(all_cases[0], dict) else 'Not a dict'}")
                    
                    # Look for our specific account
                    account_cases = [case for case in all_cases if case.get('account_id') == account_id]
                    print(f"🔍 DEBUG: Cases for account {account_id}: {len(account_cases)}")
                    
                    if account_cases:
                        print(f"🔍 DEBUG: Found matching cases: {account_cases}")
                        cases = account_cases
                        cases_found = True
                    else:
                        # Show all unique account_ids to help debug
                        account_ids = list(set([case.get('account_id') for case in all_cases if case.get('account_id') is not None]))
                        print(f"🔍 DEBUG: Available account_ids in cases: {sorted(account_ids)}")
                        
                        # Check for different field names
                        for case in all_cases[:3]:  # Check first 3 cases
                            print(f"🔍 DEBUG: Case {case.get('id')} account fields:")
                            for key, value in case.items():
                                if 'account' in key.lower():
                                    print(f"   {key}: {value}")
                else:
                    print(f"🔍 DEBUG: No cases found in the system at all")
            else:
                print(f"🔍 DEBUG: All cases endpoint failed: {all_cases_response.status_code}")
                print(f"🔍 DEBUG: Error response: {all_cases_response.text}")

        except Exception as e:
            print(f"🔍 DEBUG: Exception getting all cases: {str(e)}")
            print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")

        # Now try the specific endpoints
        for endpoint in case_endpoints:
            if cases_found and endpoint != f"/api/cases/":  # Skip others if we already found cases
                continue
                
            try:
                print(f"🔍 DEBUG: Trying endpoint: {fastapi_url}{endpoint}")
                case_response = requests.get(f"{fastapi_url}{endpoint}", headers=headers, timeout=10)
                
                debug_entry = {
                    'endpoint': endpoint,
                    'status_code': case_response.status_code,
                    'headers': dict(case_response.headers),
                    'url': f"{fastapi_url}{endpoint}"
                }
                
                print(f"🔍 DEBUG: Endpoint {endpoint} returned status {case_response.status_code}")
                
                if case_response.status_code == 200:
                    try:
                        case_data = case_response.json()
                        debug_entry['response_type'] = type(case_data).__name__
                        debug_entry['response_keys'] = list(case_data.keys()) if isinstance(case_data, dict) else 'Not a dict'
                        
                        print(f"🔍 DEBUG: Response type: {type(case_data)}")
                        print(f"🔍 DEBUG: Response data: {case_data}")
                        
                        # Handle different response formats
                        if isinstance(case_data, list):
                            endpoint_cases = case_data
                        elif isinstance(case_data, dict):
                            if 'id' in case_data:  # Single case object
                                endpoint_cases = [case_data]
                            else:  # Paginated response
                                endpoint_cases = case_data.get('items', case_data.get('data', []))
                        else:
                            endpoint_cases = []
                        
                        debug_entry['cases_count'] = len(endpoint_cases)
                        
                        if endpoint_cases and not cases_found:
                            cases = endpoint_cases
                            cases_found = True
                            print(f"✅ DEBUG: Successfully loaded {len(cases)} cases from {endpoint}")
                            
                            for i, case in enumerate(cases[:2]):  # Show first 2 cases
                                print(f"🔍 DEBUG: Case {i+1} data: {case}")
                                
                    except Exception as json_error:
                        debug_entry['json_error'] = str(json_error)
                        debug_entry['raw_response'] = case_response.text[:500]
                        print(f"🔍 DEBUG: JSON parsing error: {json_error}")
                        print(f"🔍 DEBUG: Raw response: {case_response.text[:500]}")
                        
                else:
                    debug_entry['error_response'] = case_response.text[:500]
                    print(f"🔍 DEBUG: Error response: {case_response.text}")
                
                debug_info.append(debug_entry)
                
            except Exception as e:
                print(f"🔍 DEBUG: Exception with endpoint {endpoint}: {str(e)}")
                debug_info.append({
                    'endpoint': endpoint,
                    'exception': str(e)
                })

        # Final debug summary
        print(f"🔍 DEBUG: === FINAL CASES SUMMARY ===")
        print(f"🔍 DEBUG: Cases found: {cases_found}")
        print(f"🔍 DEBUG: Number of cases: {len(cases)}")
        print(f"🔍 DEBUG: Account ID we're looking for: {account_id}")

        if cases:
            for case in cases:
                print(f"🔍 DEBUG: Case summary - ID: {case.get('id')}, Number: {case.get('case_number')}, Account: {case.get('account_id')}")

        # Store debug info in a place we can access it in the template
        account['debug_cases_info'] = debug_info
        account['debug_cases_summary'] = {
            'target_account_id': account_id,
            'cases_found': cases_found,
            'cases_count': len(cases),
            'endpoints_tried': len(debug_info)
        }

        print(f"🔍 DEBUG: Debug info stored in account object for template")
        
        print(f"📊 Final data summary for account {account_id}:")
        print(f"   - Account: {account.get('account_name', 'Unknown')}")
        print(f"   - Contacts: {len(contacts)}")
        print(f"   - Loans: {len(loans)}")
        print(f"   - Assets: {len(assets)}")
        print(f"   - Cases: {len(cases)}")
        
        # Data validation and cleaning
        try:
            # Ensure all data is properly formatted
            contacts = contacts or []
            loans = loans or []
            assets = assets or []
            cases = cases or []
            
            # Check for problematic data in contacts
            for i, contact in enumerate(contacts):
                if not isinstance(contact, dict):
                    print(f"⚠️ Contact {i} is not a dict: {type(contact)}")
                    contacts[i] = {}
            
            # Check for problematic data in loans  
            for i, loan in enumerate(loans):
                if not isinstance(loan, dict):
                    print(f"⚠️ Loan {i} is not a dict: {type(loan)}")
                    loans[i] = {}
            
            # Check for problematic data in assets
            for i, asset in enumerate(assets):
                if not isinstance(asset, dict):
                    print(f"⚠️ Asset {i} is not a dict: {type(asset)}")
                    assets[i] = {}

            # Check for problematic data in cases
            for i, case in enumerate(cases):
                if not isinstance(case, dict):
                    print(f"⚠️ Case {i} is not a dict: {type(case)}")
                    cases[i] = {}
            
            print(f"🎯 Attempting to render template for account {account_id}")
            
            return render_template('accounts/detail.html', 
                                 account=account, 
                                 contacts=contacts, 
                                 loans=loans, 
                                 assets=assets,
                                 cases=cases)
        
        except Exception as template_error:
            print(f"❌ Template rendering error for account {account_id}: {str(template_error)}")
            print(f"❌ Template error type: {type(template_error).__name__}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            
            # Try with minimal safe data
            safe_account = {
                'id': account.get('id', account_id),
                'account_name': account.get('account_name', 'Unknown Account'),
                'account_number': account.get('account_number', 'Unknown'),
                'status': account.get('status', 'Unknown'),
                'account_type': account.get('account_type', 'Unknown'),
                'created_at': account.get('created_at', None)
            }
            
            flash(f'Template error for account {account_id}: {str(template_error)}', 'error')
            return render_template('accounts/detail.html', 
                                 account=safe_account, 
                                 contacts=[], 
                                 loans=[], 
                                 assets=[],
                                 cases=[])
        
    except requests.exceptions.RequestException as req_error:
        print(f"❌ Request error for account {account_id}: {str(req_error)}")
        flash(f'Network error loading account {account_id}: {str(req_error)}', 'error')
        return redirect(url_for('accounts.index'))
        
    except Exception as e:
        print(f"❌ Unexpected error for account {account_id}: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash(f'Unexpected error loading account {account_id}: {str(e)}', 'error')
        return redirect(url_for('accounts.index'))

@accounts_bp.route('/<int:account_id>/edit')
def edit(account_id):
    """Route for editing accounts"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        access_token = session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        from flask import current_app
        fastapi_url = current_app.config['FASTAPI_BASE_URL']
        response = requests.get(
            f"{fastapi_url}/api/accounts/{account_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json()
            return render_template('accounts/edit.html', account=account)
        else:
            flash('Account not found.', 'error')
            return redirect(url_for('accounts.index'))
    
    except Exception as e:
        print(f"Error loading account for edit: {e}")
        flash('Error loading account for editing.', 'error')
        return redirect(url_for('accounts.index'))

@accounts_bp.route('/<int:account_id>/update', methods=['POST'])
def update(account_id):
    """Route for updating accounts"""
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
        
        from flask import current_app
        fastapi_url = current_app.config['FASTAPI_BASE_URL']
        response = requests.put(
            f"{fastapi_url}/api/accounts/{account_id}",
            headers=headers,
            json=account_data,
            timeout=10
        )
        
        if response.status_code == 200:
            flash('Account updated successfully!', 'success')
            return redirect(url_for('accounts.detail', account_id=account_id))
        else:
            flash('Error updating account. Please try again.', 'error')
            return redirect(url_for('accounts.edit', account_id=account_id))
    
    except Exception as e:
        print(f"Error updating account: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('accounts.edit', account_id=account_id))