# routes/assets.py - Assets Blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.auth import require_auth
from utils.api_client import APIClient

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/')
@require_auth
def index():
    try:
        search = request.args.get('search', '')
        make = request.args.get('make', '')
        asset_type = request.args.get('type', '')
        
        params = {'limit': 100}
        if search:
            params['search'] = search
        if make:
            params['Make'] = make
        if asset_type:
            params['asset_type'] = asset_type
        
        response = APIClient.get('/assets/', params)
        assets = response.get('items', []) if isinstance(response, dict) else response
        
        # Get unique makes for filter
        makes = sorted(list(set(asset.get('Make', '') for asset in assets if asset.get('Make'))))
        
    except Exception as e:
        flash(f'Error loading assets: {str(e)}', 'error')
        assets = []
        makes = []
    
    return render_template('assets/index.html', 
                         assets=assets,
                         makes=makes,
                         search=search,
                         selected_make=make,
                         asset_type=asset_type)