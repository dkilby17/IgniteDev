# routes/cases.py - Updated with Enhanced Dynamic Filters Support
from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.auth import require_auth
from utils.api_client import APIClient
import logging

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/')
@require_auth
def index():
    try:
        # Get filter parameters
        search = request.args.get('search', '')
        status = request.args.get('status', 'New')  # Default to 'New'
        case_type = request.args.get('type', '')
        financial_institution = request.args.get('financial_institution', '')
        priority = request.args.get('priority', '')
        
        # Get sorting parameters
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 50
        skip = (page - 1) * per_page
        
        # Special handling: If user explicitly selects "All Statuses", don't filter by status
        if request.args.get('status') == '':
            status = ''
        
        print(f"🔍 FLASK ROUTE DEBUG:")
        print(f"   Sort by: {sort_by}")
        print(f"   Sort order: {sort_order}")
        print(f"   Status filter: '{status}'")
        print(f"   All args: {dict(request.args)}")
        
        # STEP 1: Get dynamic filters from FastAPI backend with enhanced error handling
        dynamic_filters = {}
        filter_api_success = False
        
        try:
            print(f"🔍 Calling filter API...")
            filter_response = APIClient.get('/cases/filters')
            print(f"   🔍 Filter API Response type: {type(filter_response)}")
            print(f"   🔍 Filter API Response content: {filter_response}")
            
            if isinstance(filter_response, dict) and 'filters' in filter_response:
                dynamic_filters = filter_response['filters']
                filter_api_success = True
                print(f"   ✅ SUCCESS: Loaded {len(dynamic_filters)} dynamic filter categories")
                print(f"   📋 Available categories: {list(dynamic_filters.keys())}")
                
                # Debug each category
                for category, options in dynamic_filters.items():
                    print(f"     - {category}: {len(options)} options")
                    if options:
                        print(f"       Sample: {options[:3]}")
                    else:
                        print(f"       (empty)")
                        
            elif isinstance(filter_response, dict) and 'error' in filter_response:
                print(f"   ❌ Filter API returned error: {filter_response.get('error')}")
                # Check if there are fallback filters in the response
                if 'filters' in filter_response:
                    dynamic_filters = filter_response['filters']
                    filter_api_success = True
                    print(f"   🔄 Using fallback filters from API response")
                    
            else:
                print(f"   ⚠️ Unexpected filter response format: {filter_response}")
                
        except Exception as filter_error:
            print(f"   ❌ Error loading dynamic filters: {filter_error}")
            import traceback
            print(f"   ❌ Traceback: {traceback.format_exc()}")

        # If filter API failed or returned empty data, use hardcoded fallback
        if not filter_api_success or not dynamic_filters:
            print(f"   🔄 Using hardcoded fallback filters")
            dynamic_filters = {
                'case_status': ['New', 'Open', 'In Progress', 'Pending', 'Resolved', 'Closed', 'Escalated'],
                'case_type': ['General', 'Payment Issue', 'Account Inquiry', 'Technical Support', 'Complaint', 'Collections', 'Delinquency'],
                'case_priority': ['Low', 'Medium', 'High', 'Urgent'],
                'financial_institution': ['Cleo Financial', 'OpenRoad', 'TD Bank', 'RBC', 'BMO']
            }
            filter_api_success = False

        # Ensure all expected categories exist (even if empty)
        expected_categories = ['case_status', 'case_type', 'case_priority', 'financial_institution']
        for category in expected_categories:
            if category not in dynamic_filters:
                dynamic_filters[category] = []
                print(f"   ⚠️ Added missing category: {category}")
        
        # STEP 2: Build API parameters for cases
        params = {
            'limit': per_page,
            'skip': skip
        }
        
        # Add filter parameters if provided
        if search:
            params['search'] = search
        if status:  # Only add status filter if not empty
            params['status'] = status
        if case_type:
            params['case_type'] = case_type
        if financial_institution:
            params['financial_institution'] = financial_institution
        if priority:
            params['priority'] = priority
        
        # Add sorting parameters
        if sort_by and sort_order:
            params['sort_by'] = sort_by
            params['sort_order'] = sort_order
            print(f"   Added sort params to API: sort_by={sort_by}, sort_order={sort_order}")
        
        print(f"   Final API params: {params}")
        
        # STEP 3: Make API call to get cases
        response = APIClient.get('/cases/', params)
        print(f"   API Response type: {type(response)}")
        
        # Handle different response formats
        if isinstance(response, dict):
            cases = response.get('items', [])
            total = response.get('total', 0)
            total_pages = response.get('pages', 1)
            has_next = response.get('page', 1) < total_pages
            has_prev = response.get('page', 1) > 1
            print(f"   Got {len(cases)} cases from API")
        else:
            # Fallback for simple list response
            cases = response if isinstance(response, list) else []
            total = len(cases)
            total_pages = 1
            has_next = False
            has_prev = False
            print(f"   Fallback: Got {len(cases)} cases, doing client-side sorting")
            
            # If API doesn't support sorting, do client-side sorting
            if cases and sort_by:
                print(f"   Applying client-side sorting: {sort_by} {sort_order}")
                cases = sort_cases_client_side(cases, sort_by, sort_order)
                print(f"   Client-side sorting complete")
        
    except Exception as e:
        print(f"❌ Error in cases route: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        flash(f'Error loading cases: {str(e)}', 'error')
        cases = []
        total = 0
        total_pages = 1
        has_next = False
        has_prev = False
        dynamic_filters = {
            'case_status': ['New', 'Open', 'In Progress', 'Closed'],
            'case_type': ['General', 'Payment Issue', 'Complaint'],
            'case_priority': ['Low', 'Medium', 'High'],
            'financial_institution': []
        }
        filter_api_success = False
    
    print(f"🎯 FINAL TEMPLATE DATA:")
    print(f"   - Cases: {len(cases)}")
    print(f"   - Filter API Success: {filter_api_success}")
    print(f"   - Dynamic filters: {list(dynamic_filters.keys())}")
    print(f"   - Status options: {dynamic_filters.get('case_status', [])}")
    print(f"   - Case type options: {dynamic_filters.get('case_type', [])}")
    print(f"   - Priority options: {dynamic_filters.get('case_priority', [])}")
    print(f"   - FI options: {len(dynamic_filters.get('financial_institution', []))}")
    print(f"   - Current status filter: '{status}'")
    print(f"   - Current case_type filter: '{case_type}'")
    
    return render_template('cases/index.html', 
                         cases=cases,
                         dynamic_filters=dynamic_filters,  # ✅ Pass dynamic filters
                         filter_api_success=filter_api_success,  # ✅ Pass API success flag
                         search=search,
                         status=status,
                         case_type=case_type,
                         financial_institution=financial_institution,
                         priority=priority,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         page=page,
                         total=total,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev)

def sort_cases_client_side(cases, sort_by, sort_order):
    """
    Client-side sorting function for when API doesn't support sorting
    """
    if not cases or not sort_by:
        return cases
    
    reverse = sort_order == 'desc'
    print(f"   🔄 Client-side sorting {len(cases)} cases by {sort_by} ({sort_order})")
    
    try:
        if sort_by == 'id':
            sorted_cases = sorted(cases, key=lambda x: x.get('id', 0), reverse=reverse)
        
        elif sort_by == 'subject':
            sorted_cases = sorted(cases, key=lambda x: (x.get('subject') or '').lower(), reverse=reverse)
        
        elif sort_by == 'case_type':
            sorted_cases = sorted(cases, key=lambda x: (x.get('case_type') or '').lower(), reverse=reverse)
        
        elif sort_by == 'status':
            sorted_cases = sorted(cases, key=lambda x: (x.get('status') or '').lower(), reverse=reverse)
        
        elif sort_by == 'priority':  # Add priority sorting
            sorted_cases = sorted(cases, key=lambda x: (x.get('priority') or '').lower(), reverse=reverse)
        
        elif sort_by == 'created_at':
            sorted_cases = sorted(cases, key=lambda x: x.get('created_at', ''), reverse=reverse)
        
        elif sort_by == 'financial_institution':
            def get_fi(case):
                # Try to get financial institution from loan, account, or contact
                if case.get('loan', {}).get('financial_institution'):
                    return case['loan']['financial_institution'].lower()
                elif case.get('account', {}).get('financial_institution'):
                    return case['account']['financial_institution'].lower()
                elif case.get('contact', {}).get('financial_institution'):
                    return case['contact']['financial_institution'].lower()
                return ''
            
            sorted_cases = sorted(cases, key=get_fi, reverse=reverse)
        
        elif sort_by == 'days_past_due':
            def get_days_past_due(case):
                loan = case.get('loan', {})
                days = loan.get('days_past_due')
                return days if days is not None else -1  # Put N/A values at the beginning
            
            sorted_cases = sorted(cases, key=get_days_past_due, reverse=reverse)
        
        elif sort_by == 'total_owing':
            def get_total_owing(case):
                loan = case.get('loan', {})
                past_due = float(loan.get('past_due_amount') or 0)
                fees = float(loan.get('past_due_fees') or 0)
                total = past_due + fees
                if total == 0 and case.get('amount_involved'):
                    total = float(case.get('amount_involved') or 0)
                return total
            
            sorted_cases = sorted(cases, key=get_total_owing, reverse=reverse)
        
        else:
            # Default to created_at if unknown sort field
            print(f"   ⚠️ Unknown sort field: {sort_by}, using created_at")
            sorted_cases = sorted(cases, key=lambda x: x.get('created_at', ''), reverse=reverse)
        
        print(f"   ✅ Client-side sorting complete")
        return sorted_cases
            
    except Exception as e:
        # If sorting fails, return original list
        print(f"   ❌ Sorting error: {e}")
        return cases

@cases_bp.route('/<int:case_id>')
@require_auth
def detail(case_id):
    try:
        case = APIClient.get(f'/cases/{case_id}')
        # Get related loan and account info
        loan = None
        account = None
        if case.get('loan_id'):
            loan = APIClient.get(f'/loans/{case["loan_id"]}')
        if case.get('account_id'):
            account = APIClient.get(f'/accounts/{case["account_id"]}')
            
    except Exception as e:
        flash(f'Error loading case: {str(e)}', 'error')
        return redirect(url_for('cases.index'))
    
    return render_template('cases/detail.html',
                         case=case,
                         loan=loan,
                         account=account)

@cases_bp.route('/new')
@require_auth
def new():
    """Display form to create a new case"""
    # This would render a form for creating new cases
    return render_template('cases/new.html')

@cases_bp.route('/<int:case_id>/edit')
@require_auth
def edit(case_id):
    """Display form to edit an existing case"""
    try:
        case = APIClient.get(f'/cases/{case_id}')
    except Exception as e:
        flash(f'Error loading case: {str(e)}', 'error')
        return redirect(url_for('cases.index'))
    
    return render_template('cases/edit.html', case=case)