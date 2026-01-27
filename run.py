from app import create_app, db, socketio

app = create_app()

with app.app_context():
    from app.models import *
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True, allow_unsafe_werkzeug=True)
