from app import create_app, db
from sqlalchemy import inspect, text
from datetime import datetime

def migrate_database():
    """Run all database migrations"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Migration 1: Add created_at to payment table
            if 'payment' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('payment')]
                if 'created_at' not in columns:
                    print("Adding 'created_at' column to Payment table...")
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            ALTER TABLE payment 
                            ADD COLUMN created_at DATETIME
                        """))
                        conn.commit()
                        
                        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        conn.execute(text(f"""
                            UPDATE payment 
                            SET created_at = '{current_time}' 
                            WHERE created_at IS NULL
                        """))
                        conn.commit()
                    print("✓ Successfully added 'created_at' column to Payment table")
                else:
                    print("✓ 'created_at' column already exists in Payment table")
            
            # Migration 2: Add user_id to author table
            if 'author' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('author')]
                if 'user_id' not in columns:
                    print("Adding 'user_id' column to Author table...")
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            ALTER TABLE author 
                            ADD COLUMN user_id INTEGER
                        """))
                        conn.commit()
                    print("✓ Successfully added 'user_id' column to Author table")
                else:
                    print("✓ 'user_id' column already exists in Author table")
            
            # Migration 3: Create book_rating table if it doesn't exist
            if 'book_rating' not in inspector.get_table_names():
                print("Creating 'book_rating' table...")
                db.create_all()
                print("✓ Successfully created 'book_rating' table")
            else:
                print("✓ 'book_rating' table already exists")
            
            # Migration 4: Add profile_image to user table
            if 'user' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('user')]
                if 'profile_image' not in columns:
                    print("Adding 'profile_image' column to User table...")
                    with db.engine.connect() as conn:
                        conn.execute(text("""
                            ALTER TABLE user 
                            ADD COLUMN profile_image VARCHAR(255)
                        """))
                        conn.commit()
                    print("✓ Successfully added 'profile_image' column to User table")
                else:
                    print("✓ 'profile_image' column already exists in User table")
                
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            print("\nManual migration required:")
            print("1. Open your database with SQLite browser")
            print("2. Run: ALTER TABLE author ADD COLUMN user_id INTEGER")
            print("3. Run: ALTER TABLE payment ADD COLUMN created_at DATETIME")
            print("4. Run: UPDATE payment SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            print("5. Run: ALTER TABLE user ADD COLUMN profile_image VARCHAR(255)")

if __name__ == '__main__':
    migrate_database()
