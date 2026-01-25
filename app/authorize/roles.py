"""
Role-based access control decorators and utilities
"""
from functools import wraps
from flask import abort, jsonify
from flask_jwt_extended import get_jwt_identity
from flask_login import current_user
from app.models import User


def role_required(*allowed_roles):
    """
    Decorator to check if user has required role(s)
    Usage: @role_required('admin', 'author')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401, description="Authentication required")
            
            if current_user.role not in allowed_roles:
                abort(403, description=f"Access denied. Required roles: {', '.join(allowed_roles)}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_role_required(*allowed_roles):
    """
    API decorator to check if user has required role(s) using JWT
    Usage: @api_role_required('admin', 'author')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_username = get_jwt_identity()
            if not current_username:
                return {'message': 'Authentication required'}, 401
            
            user = User.query.filter_by(username=current_username).first()
            if not user:
                return {'message': 'User not found'}, 404
            
            if user.role not in allowed_roles:
                return {
                    'message': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                    'your_role': user.role
                }, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def author_or_admin_required(f):
    """Decorator for web routes - requires author or admin role"""
    return role_required('admin', 'author')(f)


def api_author_or_admin_required(f):
    """Decorator for API routes - requires author or admin role"""
    return api_role_required('admin', 'author')(f)


def get_current_user_author():
    """Get Author profile for current user if they are an author"""
    if not current_user.is_authenticated:
        return None
    
    if current_user.role != 'author':
        return None
    
    from app.models import Author
    return Author.query.filter_by(user_id=current_user.id).first()


def get_current_user_author_api():
    """Get Author profile for current user from JWT if they are an author"""
    current_username = get_jwt_identity()
    if not current_username:
        return None
    
    user = User.query.filter_by(username=current_username).first()
    if not user or user.role != 'author':
        return None
    
    from app.models import Author
    return Author.query.filter_by(user_id=user.id).first()
