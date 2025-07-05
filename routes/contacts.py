# routes/contacts.py - Contacts Blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.auth import require_auth
from utils.api_client import APIClient

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/')
@require_auth
def index():
    try:
        search = request.args.get('search', '')
        contact_type = request.args.get('type', '')
        
        params = {'limit': 100}
        if search:
            params['search'] = search
        if contact_type:
            params['contact_type'] = contact_type
        
        response = APIClient.get('/contacts/', params)
        contacts = response.get('items', []) if isinstance(response, dict) else response
        
    except Exception as e:
        flash(f'Error loading contacts: {str(e)}', 'error')
        contacts = []
    
    return render_template('contacts/index.html', 
                         contacts=contacts,
                         search=search,
                         contact_type=contact_type)

@contacts_bp.route('/<int:contact_id>')
@require_auth
def detail(contact_id):
    try:
        contact = APIClient.get(f'/contacts/{contact_id}')
        # Get related loans and cases
        loans = APIClient.get('/loans/', {'contact_id': contact_id})
        cases = APIClient.get('/cases/', {'contact_id': contact_id})
        
        loans = loans.get('items', []) if isinstance(loans, dict) else loans
        cases = cases.get('items', []) if isinstance(cases, dict) else cases
        
    except Exception as e:
        flash(f'Error loading contact: {str(e)}', 'error')
        return redirect(url_for('contacts.index'))
    
    return render_template('contacts/detail.html',
                         contact=contact,
                         loans=loans,
                         cases=cases)