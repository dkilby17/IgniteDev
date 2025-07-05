# routes/admin.py - Fixed admin routes with correct template paths

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from utils.auth import (
    require_admin, require_admin_permission, make_api_request, 
    get_admin_context, AdminPermissions, has_admin_permission, handle_admin_error
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ========================================
# MAIN ADMIN DASHBOARD
# ========================================

@admin_bp.route('/')
@require_admin
def admin_dashboard():
    """Main admin dashboard - FIXED to handle missing template"""
    
    # Get admin context for template
    admin_context = get_admin_context()
    
    # Get query parameters for filtering and pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    mfa_filter = request.args.get('mfa', '')
    
    # Get stats
    stats_response = make_api_request('/admin/stats')
    stats = stats_response.json() if stats_response and stats_response.status_code == 200 else {}
    
    # Get available roles
    roles_response = make_api_request('/admin/roles')
    available_roles = []
    if roles_response and roles_response.status_code == 200:
        roles_data = roles_response.json()
        available_roles = roles_data.get('available_roles', [])
    
    # Build query parameters for users
    params = {
        'page': page,
        'per_page': per_page
    }
    
    if search:
        params['search'] = search
    if role_filter:
        params['role'] = role_filter
    if status_filter:
        params['active_only'] = status_filter == 'active'
    if mfa_filter:
        params['mfa_enabled'] = mfa_filter == 'enabled'
    
    # Get users
    users_response = make_api_request('/admin/users?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
    users_data = {}
    users = []
    pagination = None
    
    if users_response and users_response.status_code == 200:
        users_data = users_response.json()
        users = users_data.get('users', [])
        
        # Create pagination object
        class Pagination:
            def __init__(self, page, per_page, total, has_prev, has_next, prev_num, next_num):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.has_prev = has_prev
                self.has_next = has_next
                self.prev_num = prev_num
                self.next_num = next_num
        
        pagination = Pagination(
            page=users_data.get('page', 1),
            per_page=users_data.get('per_page', per_page),
            total=users_data.get('total', 0),
            has_prev=users_data.get('has_prev', False),
            has_next=users_data.get('has_next', False),
            prev_num=users_data.get('page', 1) - 1 if users_data.get('has_prev', False) else None,
            next_num=users_data.get('page', 1) + 1 if users_data.get('has_next', False) else None
        )
    
    # Try to render the admin template with multiple fallback options
    template_names = ['admin.html', 'admin/admin.html', 'dashboard.html']
    
    for template_name in template_names:
        try:
            return render_template(template_name, 
                                 stats=stats,
                                 users=users,
                                 available_roles=available_roles,
                                 pagination=pagination,
                                 admin_context=admin_context,
                                 current_section='dashboard',
                                 current_filters={
                                     'search': search,
                                     'role': role_filter,
                                     'status': status_filter,
                                     'mfa': mfa_filter
                                 })
        except:
            continue
    
    # If no template found, create a simple fallback HTML
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - Template Missing</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .error { background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <h1>Admin Dashboard</h1>
        <div class="error">
            <h3>⚠️ Template Missing</h3>
            <p>The admin.html template was not found. Please create the template file in your templates directory.</p>
            <p>Expected locations:</p>
            <ul>
                <li>templates/admin.html</li>
                <li>templates/admin/admin.html</li>
            </ul>
        </div>
        
        <h2>Current Stats</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>Total Users</h3>
                <p style="font-size: 24px; color: #2563eb;">""" + str(stats.get('total_users', 0)) + """</p>
            </div>
            <div class="stat-card">
                <h3>Active Users</h3>
                <p style="font-size: 24px; color: #059669;">""" + str(stats.get('active_users', 0)) + """</p>
            </div>
            <div class="stat-card">
                <h3>MFA Enabled</h3>
                <p style="font-size: 24px; color: #7c3aed;">""" + str(stats.get('mfa_enabled_users', 0)) + """</p>
            </div>
            <div class="stat-card">
                <h3>Locked Users</h3>
                <p style="font-size: 24px; color: #dc2626;">""" + str(stats.get('locked_users', 0)) + """</p>
            </div>
        </div>
        
        <h2>Users (""" + str(len(users)) + """ found)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background: #f3f4f6;">
                <th style="padding: 10px;">Username</th>
                <th style="padding: 10px;">Email</th>
                <th style="padding: 10px;">Active</th>
                <th style="padding: 10px;">MFA</th>
                <th style="padding: 10px;">Roles</th>
            </tr>""" + ''.join([f"""
            <tr>
                <td style="padding: 10px;">{user.get('username', 'N/A')}</td>
                <td style="padding: 10px;">{user.get('email', 'N/A')}</td>
                <td style="padding: 10px;">{'✅' if user.get('is_active') else '❌'}</td>
                <td style="padding: 10px;">{'✅' if user.get('mfa_enabled') else '❌'}</td>
                <td style="padding: 10px;">{', '.join(user.get('roles', []))}</td>
            </tr>""" for user in users]) + """
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: #f0f9ff; border-radius: 5px;">
            <h3>📋 Next Steps:</h3>
            <ol>
                <li>Create the <code>admin.html</code> template in your <code>templates</code> directory</li>
                <li>Copy the admin template content from the artifacts provided earlier</li>
                <li>Refresh this page to see the full admin interface</li>
            </ol>
            <p><a href="/dashboard">← Back to Dashboard</a></p>
        </div>
    </body>
    </html>
    """

# ========================================
# USER MANAGEMENT SECTION
# ========================================

@admin_bp.route('/users')
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def user_management():
    """User management section"""
    
    # Get query parameters for filtering and pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    mfa_filter = request.args.get('mfa', '')
    
    # Get admin context
    admin_context = get_admin_context()
    
    # Get stats
    stats_response = make_api_request('/admin/stats')
    stats = stats_response.json() if stats_response and stats_response.status_code == 200 else {}
    
    # Get available roles
    roles_response = make_api_request('/admin/roles')
    available_roles = []
    if roles_response and roles_response.status_code == 200:
        roles_data = roles_response.json()
        available_roles = roles_data.get('available_roles', [])
    
    # Build query parameters for users
    params = {
        'page': page,
        'per_page': per_page
    }
    
    if search:
        params['search'] = search
    if role_filter:
        params['role'] = role_filter
    if status_filter:
        params['active_only'] = status_filter == 'active'
    if mfa_filter:
        params['mfa_enabled'] = mfa_filter == 'enabled'
    
    # Get users
    users_response = make_api_request('/admin/users?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
    users_data = {}
    users = []
    pagination = None
    
    if users_response and users_response.status_code == 200:
        users_data = users_response.json()
        users = users_data.get('users', [])
        
        # Create pagination object
        class Pagination:
            def __init__(self, page, per_page, total, has_prev, has_next, prev_num, next_num):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.has_prev = has_prev
                self.has_next = has_next
                self.prev_num = prev_num
                self.next_num = next_num
        
        pagination = Pagination(
            page=users_data.get('page', 1),
            per_page=users_data.get('per_page', per_page),
            total=users_data.get('total', 0),
            has_prev=users_data.get('has_prev', False),
            has_next=users_data.get('has_next', False),
            prev_num=users_data.get('page', 1) - 1 if users_data.get('has_prev', False) else None,
            next_num=users_data.get('page', 1) + 1 if users_data.get('has_next', False) else None
        )
    
    # Create a separate users template or check if it exists, fallback to main template
    try:
        return render_template('admin/users.html', 
                             stats=stats,
                             users=users,
                             available_roles=available_roles,
                             pagination=pagination,
                             admin_context=admin_context,
                             current_section='users',
                             current_filters={
                                 'search': search,
                                 'role': role_filter,
                                 'status': status_filter,
                                 'mfa': mfa_filter
                             })
    except:
        # Fallback to main admin template if users template doesn't exist
        return render_template('admin.html', 
                             stats=stats,
                             users=users,
                             available_roles=available_roles,
                             pagination=pagination,
                             admin_context=admin_context,
                             current_section='users',
                             current_filters={
                                 'search': search,
                                 'role': role_filter,
                                 'status': status_filter,
                                 'mfa': mfa_filter
                             })

# ========================================
# FILTER MANAGEMENT SECTION
# ========================================

@admin_bp.route('/filters')
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def filter_management():
    """Filter management section"""
    
    admin_context = get_admin_context()
    
    # Get filter categories
    # In your filter_management route, change this line:
    filters_response = make_api_request('/admin/filters/categories?include_inactive=true')
    filter_categories = []
    
    if filters_response and filters_response.status_code == 200:
        filter_categories = filters_response.json()
    
    # Get filter stats
    stats_response = make_api_request('/admin/filters/stats')
    filter_stats = {}
    
    if stats_response and stats_response.status_code == 200:
        filter_stats = stats_response.json()
    
    # Try to render filters template, fallback to main admin template
    try:
        return render_template('admin/filters.html',
                             filter_categories=filter_categories,
                             filter_stats=filter_stats,
                             admin_context=admin_context,
                             current_section='filters')
    except:
        # Fallback to main admin template if filters template doesn't exist
        return render_template('admin.html',
                             filter_categories=filter_categories,
                             filter_stats=filter_stats,
                             admin_context=admin_context,
                             current_section='filters')

# ========================================
# SYSTEM SETTINGS SECTION
# ========================================

@admin_bp.route('/settings')
@require_admin_permission(AdminPermissions.MANAGE_SYSTEM_SETTINGS)
def system_settings():
    """System settings section (super admin only)"""
    
    admin_context = get_admin_context()
    
    # Get system settings
    settings_response = make_api_request('/admin/system-settings')
    system_settings = {}
    
    if settings_response and settings_response.status_code == 200:
        system_settings = settings_response.json()
    
    try:
        return render_template('admin/settings.html',
                             system_settings=system_settings,
                             admin_context=admin_context,
                             current_section='settings')
    except:
        # Fallback to main admin template
        return render_template('admin.html',
                             system_settings=system_settings,
                             admin_context=admin_context,
                             current_section='settings')

# ========================================
# AUDIT LOGS SECTION
# ========================================

@admin_bp.route('/logs')
@require_admin_permission(AdminPermissions.VIEW_AUDIT_LOGS)
def audit_logs():
    """Audit logs section"""
    
    admin_context = get_admin_context()
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)
    
    # Build query parameters
    params = {
        'skip': (page - 1) * per_page,
        'limit': per_page
    }
    
    if action:
        params['action'] = action
    if user_id:
        params['user_id'] = user_id
    
    # Get audit logs
    logs_response = make_api_request('/admin/audit-logs?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
    audit_logs = {'logs': [], 'total': 0}
    
    if logs_response and logs_response.status_code == 200:
        audit_logs = logs_response.json()
    
    try:
        return render_template('admin/logs.html',
                             audit_logs=audit_logs,
                             admin_context=admin_context,
                             current_section='logs',
                             current_filters={
                                 'action': action,
                                 'user_id': user_id
                             })
    except:
        # Fallback to main admin template
        return render_template('admin.html',
                             audit_logs=audit_logs,
                             admin_context=admin_context,
                             current_section='logs',
                             current_filters={
                                 'action': action,
                                 'user_id': user_id
                             })

# ========================================
# API ROUTES FOR AJAX CALLS
# ========================================

@admin_bp.route('/api/stats')
@require_admin
def api_get_stats():
    """Get admin statistics via AJAX"""
    response = make_api_request('/admin/stats')
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'Failed to fetch stats'}), 500

@admin_bp.route('/api/users')
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_get_users():
    """Get users list via AJAX"""
    # Forward all query parameters to FastAPI
    params = dict(request.args)
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    endpoint = f'/admin/users?{query_string}' if query_string else '/admin/users'
    
    response = make_api_request(endpoint)
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'Failed to fetch users'}), 500

@admin_bp.route('/api/users/<int:user_id>')
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_get_user(user_id):
    """Get specific user details via AJAX"""
    response = make_api_request(f'/admin/users/{user_id}')
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'User not found'}), 404

@admin_bp.route('/api/users', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_create_user():
    """Create new user via AJAX"""
    data = request.get_json()
    response = make_api_request('/admin/users', method='POST', data=data)
    
    if response and response.status_code == 201:
        return jsonify(response.json()), 201
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_update_user(user_id):
    """Update user via AJAX"""
    data = request.get_json()
    response = make_api_request(f'/admin/users/{user_id}', method='PUT', data=data)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_reset_password(user_id):
    """Reset user password via AJAX"""
    data = request.get_json()
    response = make_api_request(f'/admin/users/{user_id}/reset-password', method='POST', data=data)
    
    if response and response.status_code == 200:
        return jsonify({'message': 'Password reset successfully'})
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to reset password'}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-mfa', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_reset_mfa(user_id):
    """Reset user MFA via AJAX"""
    response = make_api_request(f'/admin/users/{user_id}/reset-mfa', method='POST')
    
    if response and response.status_code == 200:
        return jsonify({'message': 'MFA reset successfully'})
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to reset MFA'}), 500

@admin_bp.route('/api/users/<int:user_id>/unlock', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_USERS)
def api_unlock_user(user_id):
    """Unlock user account via AJAX"""
    response = make_api_request(f'/admin/users/{user_id}/unlock', method='POST')
    
    if response and response.status_code == 200:
        return jsonify({'message': 'User unlocked successfully'})
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to unlock user'}), 500

@admin_bp.route('/api/roles')
@require_admin
def api_get_roles():
    """Get available roles via AJAX"""
    response = make_api_request('/admin/roles')
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'Failed to fetch roles'}), 500

# ========================================
# FILTER MANAGEMENT API ROUTES
# ========================================

@admin_bp.route('/api/filters/categories')
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_get_filter_categories():
    """Get filter categories via AJAX"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    endpoint = f'/admin/filters/categories?include_inactive={include_inactive}'
    
    response = make_api_request(endpoint)
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'Failed to fetch filter categories'}), 500

@admin_bp.route('/api/filters/categories', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_create_filter_category():
    """Create filter category via AJAX"""
    data = request.get_json()
    response = make_api_request('/admin/filters/categories', method='POST', data=data)
    
    if response and response.status_code == 201:
        return jsonify(response.json()), 201
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to create filter category'}), 500

@admin_bp.route('/api/filters/categories/<int:category_id>/options', methods=['POST'])
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_create_filter_option(category_id):
    """Create filter option via AJAX"""
    data = request.get_json()
    response = make_api_request(f'/admin/filters/categories/{category_id}/options', method='POST', data=data)
    
    if response and response.status_code == 201:
        return jsonify(response.json()), 201
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to create filter option'}), 500

@admin_bp.route('/api/filters/options/<int:option_id>/toggle', methods=['PATCH'])
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_toggle_filter_option(option_id):
    """Toggle filter option status via AJAX"""
    response = make_api_request(f'/admin/filters/options/{option_id}/toggle', method='PATCH')
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to toggle filter option'}), 500

@admin_bp.route('/api/filters/options/<int:option_id>', methods=['PUT'])
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_update_filter_option(option_id):
    """Update filter option via AJAX"""
    data = request.get_json()
    response = make_api_request(f'/admin/filters/options/{option_id}', method='PUT', data=data)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to update filter option'}), 500

@admin_bp.route('/api/filters/options/<int:option_id>', methods=['DELETE'])
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_delete_filter_option(option_id):
    """Delete filter option via AJAX"""
    response = make_api_request(f'/admin/filters/options/{option_id}', method='DELETE')
    
    if response and response.status_code == 204:
        return jsonify({'message': 'Filter option deleted successfully'})
    elif response:
        return jsonify(response.json()), response.status_code
    return jsonify({'error': 'Failed to delete filter option'}), 500

@admin_bp.route('/api/filters/stats')
@require_admin_permission(AdminPermissions.MANAGE_FILTERS)
def api_get_filter_stats():
    """Get filter statistics via AJAX"""
    response = make_api_request('/admin/filters/stats')
    if response and response.status_code == 200:
        return jsonify(response.json())
    return jsonify({'error': 'Failed to fetch filter stats'}), 500

# ========================================
# ERROR HANDLERS FOR ADMIN BLUEPRINT
# ========================================

@admin_bp.errorhandler(403)
def admin_forbidden(error):
    """Handle 403 errors in admin section"""
    logger.warning(f"Admin 403 error: {request.url}")
    return handle_admin_error(403, "You don't have permission to access this resource")

@admin_bp.errorhandler(401)
def admin_unauthorized(error):
    """Handle 401 errors in admin section"""
    logger.warning(f"Admin 401 error: {request.url}")
    return handle_admin_error(401, "Please log in to access this page")

@admin_bp.errorhandler(404)
def admin_not_found(error):
    """Handle 404 errors in admin section"""
    if request.is_json:
        return jsonify({'error': 'Resource not found'}), 404
    
    flash("The requested admin page was not found", "error")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.errorhandler(500)
def admin_server_error(error):
    """Handle 500 errors in admin section"""
    logger.error(f"Admin server error: {error}")
    
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    
    flash("An internal error occurred in the admin panel", "error")
    return redirect(url_for('admin.admin_dashboard'))