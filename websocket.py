"""
WebSocket implementation using Flask-SocketIO
"""
from flask_socketio import emit, disconnect
from flask import request, session
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_login import current_user
from app.models import User, Payment, Book, BookRating
from app.extensions import db, socketio
from datetime import datetime
import json

# Store active connections
active_connections = {}
websocket_to_user = {}


@socketio.on('connect')
def handle_connect(auth=None):
    """Handle WebSocket connection - supports both JWT and session-based auth"""
    try:
        user = None
        user_id = None
        
        # Try session-based auth first (for Flask-Login)
        try:
            # Flask-Login stores user ID in session
            # Try different possible session keys
            user_id = session.get('_user_id') or session.get('_id') or session.get('user_id')
            
            if user_id:
                # Handle both string and integer IDs
                if isinstance(user_id, str):
                    try:
                        # Handle "user_id.session_id" format or plain string
                        user_id = int(user_id.split('.')[0])
                    except:
                        try:
                            user_id = int(user_id)
                        except:
                            user_id = None
                
                if user_id:
                    user = User.query.get(user_id)
        except Exception as e:
            print(f"Session auth error: {str(e)}")
        
        # Fallback to JWT auth
        if not user and auth and isinstance(auth, dict) and 'token' in auth:
            try:
                verify_jwt_in_request()
                username = get_jwt_identity()
                if username:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        user_id = user.id
            except Exception as e:
                print(f"JWT auth error: {str(e)}")
        
        # Allow connection even without auth for public dashboard updates
        # But store user info if available
        if user and user_id:
            # Store connection with user ID
            if user_id not in active_connections:
                active_connections[user_id] = []
            active_connections[user_id].append(request.sid)
            websocket_to_user[request.sid] = user_id
            
            print(f"WebSocket connected: User {user.username} (ID: {user_id})")
            
            # Send connection confirmation
            emit('connected', {
                'message': 'Connected successfully',
                'user_id': user_id,
                'username': user.username,
                'role': user.role
            })
        else:
            # Anonymous connection for public updates
            print(f"WebSocket connected: Anonymous (SID: {request.sid})")
            emit('connected', {
                'message': 'Connected (anonymous)',
                'user_id': None,
                'username': None,
                'role': None
            })
        
        return True
    except Exception as e:
        print(f"Connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Allow connection even on error for public updates
        return True


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    user_id = websocket_to_user.get(request.sid)
    if user_id:
        if user_id in active_connections:
            if request.sid in active_connections[user_id]:
                active_connections[user_id].remove(request.sid)
            if not active_connections[user_id]:
                del active_connections[user_id]
                # Broadcast offline status
                socketio.emit('user_status_update', {
                    'user_id': user_id,
                    'is_online': False
                }, broadcast=True)
        del websocket_to_user[request.sid]


@socketio.on('ping')
def handle_ping():
    """Handle ping message"""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat message"""
    try:
        user_id = websocket_to_user.get(request.sid)
        if not user_id:
            emit('error', {'message': 'Not authenticated'})
            return
        
        receiver_id = data.get('receiver_id')
        message_text = data.get('message')
        
        if not message_text:
            emit('error', {'message': 'Message cannot be empty'})
            return
        
        # Create chat record
        from app.models import Chat, ChatType
        chat = Chat(
            sender_id=user_id,
            receiver_id=receiver_id,
            message=message_text,
            timestamp=datetime.utcnow()
        )
        db.session.add(chat)
        db.session.commit()
        
        # Send to receiver
        if receiver_id and receiver_id in active_connections:
            for sid in active_connections[receiver_id]:
                socketio.emit('chat_message', {
                    'chat_id': chat.id,
                    'sender_id': user_id,
                    'message': message_text,
                    'timestamp': chat.timestamp.isoformat()
                }, room=sid)
        
        # Confirm to sender
        emit('message_sent', {
            'chat_id': chat.id,
            'message': message_text,
            'timestamp': chat.timestamp.isoformat()
        })
        
    except Exception as e:
        emit('error', {'message': f'Error processing message: {str(e)}'})


def send_to_user(user_id, event, data):
    """Send message to a specific user"""
    if user_id in active_connections:
        for sid in active_connections[user_id]:
            socketio.emit(event, data, room=sid)


def broadcast_message(event, data):
    """Broadcast message to all connected users"""
    socketio.emit(event, data, broadcast=True)


def notify_new_payment(payment):
    """Notify all connected users about a new payment"""
    try:
        payment_data = {
            'id': payment.id,
            'user_id': payment.user_id,
            'username': payment.user.username if payment.user else 'Unknown',
            'book_id': payment.book_id,
            'book_title': payment.book.title if payment.book else 'Unknown',
            'price': float(payment.price),
            'created_at': payment.created_at.isoformat() if hasattr(payment, 'created_at') and payment.created_at else None,
            'type': 'Purchase'
        }
        
        # Broadcast to all connected users
        broadcast_message('new_activity', {
            'activity_type': 'payment',
            'data': payment_data
        })
    except Exception as e:
        print(f"Error notifying payment: {str(e)}")


def notify_new_book(book):
    """Notify all connected users about a new book"""
    try:
        book_data = {
            'id': book.id,
            'title': book.title,
            'price': float(book.price) if book.price else 0.0,
            'type': 'Book Added'
        }
        
        # Broadcast to all connected users
        broadcast_message('new_activity', {
            'activity_type': 'book',
            'data': book_data
        })
    except Exception as e:
        print(f"Error notifying book: {str(e)}")


def notify_new_user(user):
    """Notify all connected users about a new user registration"""
    try:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'type': 'User Registered'
        }
        
        # Broadcast to all connected users
        broadcast_message('new_activity', {
            'activity_type': 'user',
            'data': user_data
        })
    except Exception as e:
        print(f"Error notifying user: {str(e)}")


def notify_new_rating(rating):
    """Notify all connected users about a new rating"""
    try:
        rating_data = {
            'id': rating.id,
            'user_id': rating.user_id,
            'username': rating.user.username if rating.user else 'Unknown',
            'book_id': rating.book_id,
            'book_title': rating.book.title if rating.book else 'Unknown',
            'rating': rating.rating,
            'comment': rating.comment if rating.comment else '',
            'created_at': rating.created_at.isoformat() if hasattr(rating, 'created_at') and rating.created_at else None,
            'type': 'Rating'
        }
        
        # Broadcast to all connected users
        broadcast_message('new_activity', {
            'activity_type': 'rating',
            'data': rating_data
        })
    except Exception as e:
        print(f"Error notifying rating: {str(e)}")


def notify_dashboard_update():
    """Notify all connected users to refresh dashboard stats"""
    try:
        from app.models import Payment, Book, User
        from sqlalchemy import func
        
        # Get updated stats
        total_users = User.query.count()
        total_books = Book.query.count()
        total_payments = Payment.query.count()
        all_payments = Payment.query.all()
        total_revenue = sum(float(p.price) for p in all_payments)
        
        stats = {
            'total_users': total_users,
            'total_books': total_books,
            'total_payments': total_payments,
            'total_revenue': total_revenue
        }
        
        # Broadcast to all connected users
        broadcast_message('dashboard_update', {
            'stats': stats
        })
    except Exception as e:
        print(f"Error updating dashboard: {str(e)}")
