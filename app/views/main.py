from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import * 
from app.extensions import db
from cloudinary.uploader import upload
from app.views.auth.form import *
from app.authorize.roles import author_or_admin_required
from google_drive import upload_file
from decimal import Decimal

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Default homepage - redirects to login"""
    return redirect(url_for('auth.login'))

@main.route('/home')
def home():
    """Home route - redirects based on authentication"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@main.route('/author', methods=['GET', 'POST'])
@login_required
def author():
    username = current_user.username
    form = AuthorForm()
    if form.validate_on_submit():
        author_name = form.author_name.data
        author_decs = form.author_decs.data
        gender = form.gender.data
        author_image = form.author_image.data
        
        # Upload image to Cloudinary
        cloudinary_response = upload(author_image)
        author_image_url = cloudinary_response['secure_url']

        new_author = Author(author_name=author_name,
                            author_decs=author_decs,
                            gender=gender, 
                            author_image=author_image_url)
        db.session.add(new_author)
        db.session.commit()
        flash('Author added successfully', 'success')
        return redirect(url_for('main.author'))
    
    authors = Author.query.all()
    return render_template('authors/author.html', authors=authors, form=form, username=username)

@main.route('/add_author', methods=['GET', 'POST'])
@login_required
def add_author():
    username = current_user.username
    form = AuthorForm()
    if form.validate_on_submit():
        author_name = form.author_name.data
        author_decs = form.author_decs.data
        gender = form.gender.data
        author_image = form.author_image.data
        
        # Upload image to Cloudinary
        cloudinary_response = upload(author_image)
        author_image_url = cloudinary_response['secure_url']

        new_author = Author(author_name=author_name,
                            author_decs=author_decs,
                            gender=gender, 
                            author_image=author_image_url)
        db.session.add(new_author)
        db.session.commit()
        flash('Author added successfully', 'success')
        return redirect(url_for('main.author'))
    
    return render_template('authors/add_author.html', form=form, username=username)

@main.route('/author/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_author(id):
    author = Author.query.get_or_404(id)
    form = AuthorForm(obj=author)
    if form.validate_on_submit():
        form.populate_obj(author)
        
        # Check if a new image is uploaded
        if 'author_image' in request.files:
            author_image = form.author_image.data
            cloudinary_response = upload(author_image)
            author.author_image = cloudinary_response['secure_url']
        
        db.session.commit()
        flash('Author updated successfully', 'success')
        return redirect(url_for('main.author'))
    return render_template('authors/edit_author.html', form=form, author=author)

@main.route('/author/delete/<int:id>', methods=['POST'])
@login_required
def delete_author(id):
    author = Author.query.get_or_404(id)
    db.session.delete(author)
    db.session.commit()
    flash('Author deleted successfully', 'success')
    return redirect(url_for('main.author'))

@main.route('/category', methods=['GET', 'POST'])
@login_required
def category():
    username = current_user.username
    form = CategoryForm()
    
    # Create operation
    if form.validate_on_submit():
        name = form.name.data
        
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully', 'success')
        return redirect(url_for('main.category'))
    
    # Read operation
    categories = Category.query.all()
    
    # Update operation
    if request.method == 'POST':
        if 'edit_category' in request.form:
            category_id = request.form.get('category_id')
            new_name = request.form.get('new_name')
            category = Category.query.get(category_id)
            if category:
                category.name = new_name
                db.session.commit()
                flash('Category updated successfully', 'success')
                return redirect(url_for('main.category'))
        
        # Delete operation
        elif 'delete_category' in request.form:
            category_id = request.form.get('category_id')
            category = Category.query.get(category_id)
            if category:
                db.session.delete(category)
                db.session.commit()
                flash('Category deleted successfully', 'success')
                return redirect(url_for('main.category'))
    
    return render_template('main/category.html', form=form, username=username, categories=categories)

@main.route('/profile/me', methods=['GET', 'POST'])
@login_required
def my_profile():
    """View and edit own profile"""
    user = current_user
    form = ProfileForm()
    
    # Pre-populate form with current user data
    form.email.data = user.email
    form.gender.data = user.gender
    
    if form.validate_on_submit():
        try:
            # Update user profile
            user.email = form.email.data
            user.gender = form.gender.data
            
            # Handle profile image upload
            if form.profile_image.data and hasattr(form.profile_image.data, 'filename') and allowed_file(form.profile_image.data.filename):
                cloudinary_response = upload(form.profile_image.data)
                user.profile_image = cloudinary_response['secure_url']
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('main.my_profile'))
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('user/my_profile.html', form=form, user=user, username=user.username)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Admin profile management - view all profiles"""
    username = current_user.username
    user_role = current_user.role
    
    # Only admin can access this page
    if user_role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.my_profile'))
    
    form = ProfileForm()

    if form.validate_on_submit():
        try:
            username = form.username.data
            email = form.email.data
            gender = form.gender.data
            role = form.role.data
            profile_image = form.profile_image.data

            if profile_image and allowed_file(profile_image.filename):
                cloudinary_response = upload(profile_image)
                cloudinary_url = cloudinary_response['secure_url']

                profile = User.query.filter_by(username=username).first()
                if profile:
                    profile.email = email
                    profile.gender = gender
                    profile.role = role
                    profile.profile_image = cloudinary_url
                else:
                    profile = User(
                        username=username,
                        email=email,
                        gender=gender,
                        role=role,
                        profile_image=cloudinary_url
                    )
                db.session.add(profile)
                db.session.commit()

                flash('Profile created/updated successfully', 'success')
                return redirect(url_for('main.profile'))
            else:
                flash('Invalid profile image file extension', 'error')
        except Exception as e:
            flash('Error creating/updating profile: {}'.format(str(e)), 'error')

    profiles = User.query.all()

    if request.method == 'POST':
        if 'edit_profile' in request.form:
            profile_id = request.form.get('profile_id')
            new_username = request.form.get('new_username')
            new_email = request.form.get('new_email')
            new_gender = request.form.get('new_gender')
            new_role = request.form.get('new_role')
            new_profile_image = request.files.get('new_profile_image')

            if profile_id:
                try:
                    profile_id = int(profile_id)
                except (ValueError, TypeError):
                    flash('Invalid profile ID', 'error')
                    return redirect(url_for('main.profile'))

                profile = User.query.get(profile_id)
                if profile:
                    profile.username = new_username
                    profile.email = new_email
                    profile.gender = new_gender
                    profile.role = new_role
                    
                    # Only update image if a new one is provided
                    if new_profile_image and allowed_file(new_profile_image.filename):
                        cloudinary_response = upload(new_profile_image)
                        profile.profile_image = cloudinary_response['secure_url']
                    
                    db.session.commit()
                    flash('Profile updated successfully', 'success')
                    return redirect(url_for('main.profile'))
                else:
                    flash('Profile not found', 'error')
            else:
                flash('Profile ID is required', 'error')

    return render_template('user/profile.html', form=form, profiles=profiles, username=username)

@main.route('/profile/delete/<int:id>', methods=['POST'])
@login_required
def delete_profile(id):
    """Delete a profile - Admin only"""
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.my_profile'))
    
    profile = User.query.get_or_404(id)
    
    # Prevent deleting own profile
    if profile.id == current_user.id:
        flash('You cannot delete your own profile', 'error')
        return redirect(url_for('main.profile'))
    
    db.session.delete(profile)
    db.session.commit()
    flash('Profile deleted successfully', 'success')
    return redirect(url_for('main.profile'))


@main.route('/book', methods=['GET'])
@login_required
@author_or_admin_required
def book():
    username = current_user.username
    user_role = current_user.role
    
    # Get author profile if user is an author
    author_profile = None
    if user_role == 'author':
        author_profile = Author.query.filter_by(user_id=current_user.id).first()
        if not author_profile:
            flash('Author profile not found. Please create an author profile first.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Filter books based on user role
    if user_role == 'author':
        books = Book.query.filter_by(author_id=author_profile.id).all()
    else:
        books = Book.query.all()
    
    # Create form instance for CSRF token
    form = BookForm(user=current_user)
    
    return render_template('books/book.html', books=books, form=form, username=username, user_role=user_role)

@main.route('/add_book', methods=['GET', 'POST'])
@login_required
@author_or_admin_required
def add_book():
    username = current_user.username
    user_role = current_user.role
    
    # Get author profile if user is an author
    author_profile = None
    if user_role == 'author':
        author_profile = Author.query.filter_by(user_id=current_user.id).first()
        if not author_profile:
            flash('Author profile not found. Please create an author profile first.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Initialize form with filtered author choices
    form = BookForm(user=current_user)
    
    if form.validate_on_submit():
        # Retrieve form data
        title = form.title.data
        description = form.description.data
        price = form.price.data
        publisher = form.publisher.data
        author_id = form.author.data
        category_id = form.category.data
        book_image = form.image.data 
        book_pdf = form.file.data
        
        # Validate author access: authors can only create books for themselves
        if user_role == 'author':
            if author_profile.id != author_id:
                flash('Authors can only create books for themselves', 'error')
                return redirect(url_for('main.add_book'))
        
        # Check if the provided author_id exists
        author = Author.query.get(author_id)
        if author is None:
            flash('Author not found', 'error')
            return redirect(url_for('main.add_book'))
        
        # Check if the provided category_id exists
        category = Category.query.get(category_id)
        if category is None:
            flash('Category not found', 'error')
            return redirect(url_for('main.add_book'))
                
        # Check if all required fields are present
        if title and description and price is not None and publisher and author_id and category_id and book_image and book_pdf:
            # Handle file uploads (image and book file)
            if allowed_file(book_image.filename) and allowed_file(book_pdf.filename):
                # Upload image to Cloudinary
                cloudinary_response_image = upload(book_image)
                image_url = cloudinary_response_image['secure_url']
                
                # Upload PDF to Google Drive and get secure URL
                pdf_url = upload_file(book_pdf)
                
                # Create a new book entry
                # Convert Decimal to string for database storage (Book.price is String column)
                price_str = str(price) if price is not None else "0.00"
                
                new_book = Book(
                    title=title,
                    description=description,
                    price=price_str,
                    publisher=publisher,
                    category_id=category_id,
                    author_id=author_id,
                    book_image=image_url,
                    book_pdf=pdf_url  # Store PDF URL in the database
                )
                
                # Add the new book to the database session
                db.session.add(new_book)
                # Commit changes to the database
                db.session.commit()

                flash('Book added successfully', 'success')
                return redirect(url_for('main.book')) 
            else:
                flash('Invalid file extension for image or book file', 'error')
        else:
            flash('Please fill in all the required fields', 'error')
    
    return render_template('books/add_book.html', form=form, username=username, user_role=user_role)

@main.route('/book/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@author_or_admin_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    user_role = current_user.role
    
    # Validate author access: authors can only edit their own books
    if user_role == 'author':
        author_profile = Author.query.filter_by(user_id=current_user.id).first()
        if not author_profile or book.author_id != author_profile.id:
            flash('Authors can only edit their own books', 'error')
            return redirect(url_for('main.book'))
    
    # Create form without obj=book to avoid DecimalField conversion issues
    form = BookForm(user=current_user)
    # Manually populate form fields, converting price string to Decimal
    form.title.data = book.title
    form.description.data = book.description
    form.publisher.data = book.publisher
    form.author.data = book.author_id
    form.category.data = book.category_id
    # Convert price string to Decimal for DecimalField
    if book.price:
        try:
            form.price.data = Decimal(str(book.price))
        except (ValueError, TypeError):
            form.price.data = Decimal('0.00')
    else:
        form.price.data = Decimal('0.00')
    
    if form.validate_on_submit():
        # Validate author access again on update
        if user_role == 'author':
            author_profile = Author.query.filter_by(user_id=current_user.id).first()
            if form.author.data != author_profile.id:
                flash('Authors can only update books for themselves', 'error')
                return redirect(url_for('main.edit_book', id=id))
        
        # Check if the provided author_id exists
        author = Author.query.get(form.author.data)
        if author is None:
            flash('Author not found', 'error')
            return redirect(url_for('main.edit_book', id=id))
        
        # Check if the provided category_id exists
        category = Category.query.get(form.category.data)
        if category is None:
            flash('Category not found', 'error')
            return redirect(url_for('main.edit_book', id=id))
        
        # Update basic fields
        book.title = form.title.data
        book.description = form.description.data
        # Convert Decimal to string for database storage (Book.price is String column)
        if form.price.data is not None:
            book.price = str(form.price.data)
        book.publisher = form.publisher.data
        book.author_id = int(form.author.data) if form.author.data else book.author_id
        book.category_id = int(form.category.data) if form.category.data else book.category_id
        
        # Handle image upload if provided
        if form.image.data and allowed_file(form.image.filename):
            cloudinary_response = upload(form.image.data)
            book.book_image = cloudinary_response['secure_url']
        
        # Handle PDF upload if provided
        if form.file.data and allowed_file(form.file.filename):
            pdf_url = upload_file(form.file.data)
            book.book_pdf = pdf_url
        
        db.session.commit()
        flash('Book updated successfully', 'success')
        return redirect(url_for('main.book'))
    return render_template('books/edit_book.html', form=form, book=book, user_role=user_role)

@main.route('/book/delete/<int:id>', methods=['POST'])
@login_required
@author_or_admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    user_role = current_user.role
    
    # Validate author access: authors can only delete their own books
    if user_role == 'author':
        author_profile = Author.query.filter_by(user_id=current_user.id).first()
        if not author_profile or book.author_id != author_profile.id:
            flash('Authors can only delete their own books', 'error')
            return redirect(url_for('main.book'))
    
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully', 'success')
    return redirect(url_for('main.book'))

@main.route('/dashboard')
@login_required
def dashboard():
    username = current_user.username
    user_role = current_user.role
    
    # Get statistics
    total_users = User.query.count()
    total_books = Book.query.count()
    total_payments = Payment.query.count()
    total_categories = Category.query.count()
    total_authors = Author.query.count()
    
    # Calculate total revenue
    all_payments = Payment.query.all()
    total_revenue = sum(float(p.price) for p in all_payments)
    
    # Get users who bought many times (top buyers)
    from sqlalchemy import func
    top_buyers = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(Payment.id).label('purchase_count'),
        func.sum(Payment.price).label('total_spent')
    ).join(Payment, User.id == Payment.user_id)\
     .group_by(User.id, User.username, User.email)\
     .order_by(func.count(Payment.id).desc())\
     .limit(10).all()
    
    # Get recent payments/actions
    try:
        recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()
    except:
        recent_payments = Payment.query.order_by(Payment.id.desc()).limit(10).all()
    
    # Get recent books added
    recent_books = Book.query.order_by(Book.id.desc()).limit(5).all()
    
    # Get recent users registered
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Get user's recent actions if not admin
    user_recent_actions = []
    if user_role != 'admin':
        try:
            user_payments = Payment.query.filter_by(user_id=current_user.id)\
                .order_by(Payment.created_at.desc()).limit(5).all()
            for payment in user_payments:
                user_recent_actions.append({
                    'type': 'Purchase',
                    'description': f'Bought "{payment.book.title}"',
                    'date': payment.created_at if hasattr(payment, 'created_at') and payment.created_at else None,
                    'amount': f'${float(payment.price):.2f}'
                })
        except:
            user_payments = Payment.query.filter_by(user_id=current_user.id)\
                .order_by(Payment.id.desc()).limit(5).all()
            for payment in user_payments:
                user_recent_actions.append({
                    'type': 'Purchase',
                    'description': f'Bought "{payment.book.title}"',
                    'date': None,
                    'amount': f'${float(payment.price):.2f}'
                })
    
    # Get all recent actions for admin
    all_recent_actions = []
    if user_role == 'admin':
        # Recent payments
        for payment in recent_payments[:5]:
            all_recent_actions.append({
                'type': 'Purchase',
                'user': payment.user.username,
                'description': f'Bought "{payment.book.title}"',
                'date': payment.created_at if hasattr(payment, 'created_at') and payment.created_at else None,
                'amount': f'${float(payment.price):.2f}'
            })
        # Recent books
        for book in recent_books[:3]:
            all_recent_actions.append({
                'type': 'Book Added',
                'user': 'System',
                'description': f'New book: "{book.title}"',
                'date': None,
                'amount': None
            })
        # Recent users
        for user in recent_users[:3]:
            all_recent_actions.append({
                'type': 'User Registered',
                'user': user.username,
                'description': f'New user registered',
                'date': None,
                'amount': None
            })
        # Sort by date if available
        all_recent_actions = sorted(all_recent_actions, 
            key=lambda x: x['date'] if x['date'] else datetime.min, 
            reverse=True)[:10]
    
    return render_template('user/dashboard.html', 
                         username=username,
                         user_role=user_role,
                         total_users=total_users,
                         total_books=total_books,
                         total_payments=total_payments,
                         total_categories=total_categories,
                         total_authors=total_authors,
                         total_revenue=total_revenue,
                         top_buyers=top_buyers,
                         recent_payments=recent_payments,
                         recent_actions=all_recent_actions if user_role == 'admin' else user_recent_actions)

@main.route('/payment-history')
@login_required
def payment_history():
    username = current_user.username
    try:
        # Get all payments for the current user, ordered by most recent first
        # Handle case where created_at might not exist yet
        try:
            # Try ordering by created_at
            payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
        except Exception:
            # Fallback: order by id (most recent first) if created_at column doesn't exist
            try:
                payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.id.desc()).all()
            except Exception:
                # Last fallback: just get all payments
                payments = Payment.query.filter_by(user_id=current_user.id).all()
        
        # Calculate total spent
        total_spent = sum(float(payment.price) for payment in payments)
        
        return render_template('user/payment_history.html', 
                             payments=payments, 
                             username=username,
                             total_spent=total_spent)
    except Exception as e:
        flash(f'Error loading payment history: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@main.route('/userbook')
@login_required
def userbook():
    username = current_user.username
    # Get all books purchased by the current user
    userbooks = UserBook.query.filter_by(user_id=current_user.id).all()
    books = [ub.book for ub in userbooks if ub.book]
    return render_template('user/userbook.html', books=books, username=username)

    
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
