# routes/loans.py - Flask routes for loans
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import os
from datetime import datetime

loans_bp = Blueprint('loans', __name__, url_prefix='/loans')

FASTAPI_BASE_URL = os.environ.get('FASTAPI_BASE_URL', 'http://127.0.0.1:8000')

def get_auth_headers():
    """Get authorization headers from session"""
    access_token = session.get('access_token')
    if not access_token:
        return None
    return {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

def require_auth():
    """Check if user is authenticated"""
    if 'user_info' not in session:
        return redirect(url_for('auth.login'))
    return None

@loans_bp.route('/')
def index():
    """Loans list page"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    # Get filter parameters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    loan_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    try:
        headers = get_auth_headers()
        if not headers:
            return redirect(url_for('auth.login'))
        
        # Build API query parameters for loans
        params = {
            'skip': (page - 1) * per_page,
            'limit': per_page,
            'search': search,
            'status': status,
            'loan_type': loan_type
        }
        # Clean up empty params
        params = {k: v for k, v in params.items() if v}
        
        # Fetch loans from FastAPI
        response = requests.get(f"{FASTAPI_BASE_URL}/api/loans/", headers=headers, params=params)
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        
        response.raise_for_status()
        data = response.json()
        
        # --- PAGINATION: ROOT CAUSE ---
        # For pagination to appear, your FastAPI backend MUST return the total count of all records.
        # The response should look like this: {"items": [...], "total": 541}
        # Without the 'total' key, pagination will not work.
        if isinstance(data, dict) and 'items' in data:
            loans = data['items']
            total = data.get('total', len(loans))
        else:
            loans = data if isinstance(data, list) else []
            total = len(loans)

        # *** OPTIMIZED FIX for Customer Name ***
        # This is a more performant workaround. Instead of one API call per loan, we fetch
        # all accounts at once and map them.
        # The ideal solution remains modifying the `/api/loans/` endpoint to include the customer name.
        accounts = {}
        try:
            # Fetch all accounts to create a lookup dictionary
            # Assuming the accounts endpoint can return all accounts without pagination. 
            # If it's paginated, this logic will need to be more complex.
            accounts_response = requests.get(f"{FASTAPI_BASE_URL}/api/accounts/", headers=headers)
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                # Handle paginated or non-paginated accounts response
                accounts_list = accounts_data.get('items', accounts_data) if isinstance(accounts_data, dict) else accounts_data
                accounts = {account['id']: account.get('name', 'N/A') for account in accounts_list}
        except requests.RequestException:
            flash('Could not load account names.', 'warning')

        # Map the account names to the loans
        for loan in loans:
            loan['customer_name'] = accounts.get(loan.get('account_id'), 'N/A')
        
        # --- Pagination Calculation (Depends on 'total' from API) ---
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('loans/index.html',
                               loans=loans,
                               search=search,
                               status=status,
                               loan_type=loan_type,
                               page=page,
                               total_pages=total_pages,
                               total=total,
                               has_prev=has_prev,
                               has_next=has_next)
    
    except requests.RequestException as e:
        flash(f'Error loading loans: {str(e)}', 'error')
        # Pass all required variables to the template to prevent rendering errors on failure
        return render_template('loans/index.html', 
                               loans=[], page=1, total_pages=1, total=0, 
                               search=search, status=status, loan_type=loan_type, 
                               has_prev=False, has_next=False)


@loans_bp.route('/new')
def new():
    """New loan form"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        headers = get_auth_headers()
        if not headers:
            return redirect(url_for('auth.login'))
        
        # Load accounts and contacts for dropdowns
        accounts_response = requests.get(f"{FASTAPI_BASE_URL}/api/accounts/", headers=headers)
        contacts_response = requests.get(f"{FASTAPI_BASE_URL}/api/contacts/", headers=headers)
        
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

@loans_bp.route('/create', methods=['POST'])
def create():
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
            'loan_amount': float(request.form.get('loan_amount', 0)),
            'interest_rate': float(request.form.get('interest_rate', 0)),
            'loan_term': int(request.form.get('loan_term', 0)),
            'monthly_payment': float(request.form.get('monthly_payment', 0)),
            'principal_balance': float(request.form.get('principal_balance', 0)),
            'next_payment_date': request.form.get('next_payment_date'),
            'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
            'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None
        }
        
        # Remove None values
        loan_data = {k: v for k, v in loan_data.items() if v is not None and v != ''}
        
        response = requests.post(
            f"{FASTAPI_BASE_URL}/api/loans/",
            headers=headers,
            json=loan_data
        )
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        
        response.raise_for_status()
        
        flash('Loan created successfully!', 'success')
        return redirect(url_for('loans.index'))
        
    except requests.RequestException as e:
        flash(f'Error creating loan: {str(e)}', 'error')
        return redirect(url_for('loans.new'))
    except (ValueError, TypeError) as e:
        flash(f'Invalid form data: {str(e)}', 'error')
        return redirect(url_for('loans.new'))

@loans_bp.route('/<int:loan_id>')
def detail(loan_id):
    """Loan detail view"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        headers = get_auth_headers()
        if not headers:
            return redirect(url_for('auth.login'))
        
        # Fetch loan details
        response = requests.get(f"{FASTAPI_BASE_URL}/api/loans/{loan_id}", headers=headers)
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        elif response.status_code == 404:
            flash('Loan not found', 'error')
            return redirect(url_for('loans.index'))
        
        response.raise_for_status()
        loan = response.json()
        
        # Load related data
        account = None
        contact = None
        
        if loan.get('account_id'):
            try:
                account_response = requests.get(f"{FASTAPI_BASE_URL}/api/accounts/{loan['account_id']}", headers=headers)
                if account_response.status_code == 200:
                    account = account_response.json()
            except:
                pass
        
        if loan.get('contact_id'):
            try:
                contact_response = requests.get(f"{FASTAPI_BASE_URL}/api/contacts/{loan['contact_id']}", headers=headers)
                if contact_response.status_code == 200:
                    contact = contact_response.json()
            except:
                pass
        
        return render_template('loans/detail.html', loan=loan, account=account, contact=contact)
        
    except requests.RequestException as e:
        flash(f'Error loading loan: {str(e)}', 'error')
        return redirect(url_for('loans.index'))

@loans_bp.route('/<int:loan_id>/edit')
def edit(loan_id):
    """Edit loan form"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        headers = get_auth_headers()
        if not headers:
            return redirect(url_for('auth.login'))
        
        # Fetch loan details
        response = requests.get(f"{FASTAPI_BASE_URL}/api/loans/{loan_id}", headers=headers)
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        elif response.status_code == 404:
            flash('Loan not found', 'error')
            return redirect(url_for('loans.index'))
        
        response.raise_for_status()
        loan = response.json()
        
        # Load accounts and contacts for dropdowns
        accounts_response = requests.get(f"{FASTAPI_BASE_URL}/api/accounts/", headers=headers)
        contacts_response = requests.get(f"{FASTAPI_BASE_URL}/api/contacts/", headers=headers)
        
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
        return redirect(url_for('loans.index'))

@loans_bp.route('/<int:loan_id>/update', methods=['POST'])
def update(loan_id):
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
            'loan_amount': float(request.form.get('loan_amount', 0)),
            'interest_rate': float(request.form.get('interest_rate', 0)),
            'loan_term': int(request.form.get('loan_term', 0)),
            'monthly_payment': float(request.form.get('monthly_payment', 0)),
            'principal_balance': float(request.form.get('principal_balance', 0)),
            'next_payment_date': request.form.get('next_payment_date'),
            'account_id': int(request.form.get('account_id')) if request.form.get('account_id') else None,
            'contact_id': int(request.form.get('contact_id')) if request.form.get('contact_id') else None
        }
        
        # Remove None values
        loan_data = {k: v for k, v in loan_data.items() if v is not None and v != ''}
        
        response = requests.put(
            f"{FASTAPI_BASE_URL}/api/loans/{loan_id}",
            headers=headers,
            json=loan_data
        )
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        elif response.status_code == 404:
            flash('Loan not found', 'error')
            return redirect(url_for('loans.index'))
        
        response.raise_for_status()
        
        flash('Loan updated successfully!', 'success')
        return redirect(url_for('loans.detail', loan_id=loan_id))
        
    except requests.RequestException as e:
        flash(f'Error updating loan: {str(e)}', 'error')
        return redirect(url_for('loans.edit', loan_id=loan_id))
    except (ValueError, TypeError) as e:
        flash(f'Invalid form data: {str(e)}', 'error')
        return redirect(url_for('loans.edit', loan_id=loan_id))

@loans_bp.route('/<int:loan_id>/delete', methods=['POST'])
def delete(loan_id):
    """Delete loan"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        headers = get_auth_headers()
        if not headers:
            return redirect(url_for('auth.login'))
        
        response = requests.delete(f"{FASTAPI_BASE_URL}/api/loans/{loan_id}", headers=headers)
        
        if response.status_code == 401:
            session.clear()
            return redirect(url_for('auth.login'))
        elif response.status_code == 404:
            flash('Loan not found', 'error')
            return redirect(url_for('loans.index'))
        
        response.raise_for_status()
        
        flash('Loan deleted successfully!', 'success')
        return redirect(url_for('loans.index'))
        
    except requests.RequestException as e:
        flash(f'Error deleting loan: {str(e)}', 'error')
        return redirect(url_for('loans.detail', loan_id=loan_id))

# Simple route functions for backward compatibility
@loans_bp.route('/loans')
def loans_index():
    return redirect(url_for('loans.index'))

@loans_bp.route('/loans/new')
def loans_new():
    return redirect(url_for('loans.new'))

@loans_bp.route('/loans/<int:loan_id>')
def loans_detail(loan_id):
    return redirect(url_for('loans.detail', loan_id=loan_id))

@loans_bp.route('/loans/<int:loan_id>/edit')
def loans_edit(loan_id):
    return redirect(url_for('loans.edit', loan_id=loan_id))
