from flask import Flask , jsonify
from flask_cors import CORS
from .config import Config
from .extensions import api, db, jwt, login_manager, socketio
from .resources import *
from .models import *
from datetime import timedelta
from werkzeug.security import generate_password_hash
import cloudinary_service


def create_app():
    app = Flask(__name__)
    CORS(app)
    config = Config()
    
    app.config.from_object(config)
    app.config['JWT_TOKEN_LOCATION'] = ["headers", "cookies"]
    app.config['SECRET_KEY'] = 'thisismysecretkeydontstealit'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_SECRET_KEY"] = '07920ca637344a93a3403f4d062272f7'
    # app.config["JWT_ACCESS_TOKEN_EXPIRES"] = None

    # app.config['UPLOAD_FOLDER'] = 'assets/'
   
    api.init_app(app)
    db.init_app(app)
    jwt.init_app(app)
    register_ns(api)
    
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Import and register blueprints here
    from app.views.auth.auth import auth_bp
    from app.views.main import main
    
    print(f"Registering auth_bp: {auth_bp}")
    print(f"Registering main: {main}")
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main)
    
    print("Blueprints registered successfully")
    # app.register_blueprint(api_bp)
    
    # Initialize SocketIO with the app (after blueprints are registered)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Import websocket handlers after socketio is initialized
    try:
        import websocket
    except ImportError:
        pass  # websocket.py is optional
    
    # Create default admin account on app startup
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@elibra.com',
                password_hash=generate_password_hash('admin123'),
                gender='Other',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Default admin account created: username='admin', password='admin123'")
        else:
            # Update existing admin account to ensure correct role
            if admin_user.role != 'admin':
                admin_user.role = 'admin'
                db.session.commit()
                print("✓ Admin account role updated to 'admin'")
            else:
                print("✓ Admin account already exists with correct role")
    
    # @jwt.user_identity
    # def user_identity_lookup(user): 
    #     return user.id if user and hasattr(user, 'id') else None

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(username=identity).one_or_none()
    
    #additional claims
    @jwt.additional_claims_loader
    def make_addition_claims(identity):
        
        if identity == "admin":
            return {"is_user": True}
        return {"is_user": False}
    
    #jwt error handler
    @jwt.expired_token_loader
    def expires_token_callback(jwt_header, jwt_data):
        return jsonify({
                        "message": "Token has expired",
                        "error" : "token_expire"
                        }), 401
        
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
                        "message": "Signature verification failed",
                        "error" : "invalid_token"
                        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
                        "message": "Request doesn't contain valid token",
                        "error" : "authorization_header"
                        }), 401
        
    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jti = jwt_data['jti']
        
        token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()
        
        return token is not None 

    return app
