# routes/main.py - Dashboard and Main Routes
from flask import Blueprint, render_template, request
from utils.auth import require_auth
from utils.api_client import APIClient

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@require_auth
def dashboard():
    try:
        # Load dashboard statistics
        accounts = APIClient.get('/accounts/', {'limit': 1000})
        contacts = APIClient.get('/contacts/', {'limit': 1000})
        loans = APIClient.get('/loans/', {'limit': 1000})
        cases = APIClient.get('/cases/', {'limit': 1000})
        
        # Calculate stats
        stats = {
            'total_accounts': len(accounts.get('items', [])) if isinstance(accounts, dict) else len(accounts),
            'total_contacts': len(contacts.get('items', [])) if isinstance(contacts, dict) else len(contacts),
            'active_loans': len([l for l in (loans.get('items', []) if isinstance(loans, dict) else loans) if l.get('status') == 'Active']),
            'open_cases': len([c for c in (cases.get('items', []) if isinstance(cases, dict) else cases) if c.get('status') == 'Open'])
        }
        
    except Exception as e:
        stats = {
            'total_accounts': 0,
            'total_contacts': 0,
            'active_loans': 0,
            'open_cases': 0
        }
    
    return render_template('dashboard/index.html', stats=stats)
