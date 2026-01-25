from flask_restx import Resource, Namespace, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.resources.api_models import *
from app.models import *
from app.extensions import db
from app.authorize import authorizations
from app.authorize.roles import api_role_required, api_author_or_admin_required, get_current_user_author_api

ns_events = Namespace('events' , authorizations=authorizations)

ns_events.decorators = [jwt_required()]

@ns_events.route('/cart')
class EventListAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_list_with(cart_model)
    @jwt_required()
    def get(self):
        # Extract username from JWT token
        current_username = get_jwt_identity()

        # Get user object from the database
        user = User.query.filter_by(username=current_username).first()

        if not user:
            abort(404, message="User not found")

        # Retrieve cart items for the current user
        cart_items = Cart.query.filter_by(user_id=user.id).all()

        return cart_items, 200

    
    @ns_events.doc(security= "jsonWebToken")
    @ns_events.expect(cart_model_input)
    @ns_events.marshal_with(cart_model)
    @jwt_required()  # Ensure user is authenticated
    def post(self):
        add_cart_data = ns_events.payload

        # Extract username from JWT token
        current_username = get_jwt_identity()

        # Get user object from the database
        user = User.query.filter_by(username=current_username).first()

        # Extract book_id and quantity from the payload
        book_id = add_cart_data.get('book_id')
        quantity = add_cart_data.get('quantity', 1)  # Default to 1 if not provided

        # Check if book_id is missing
        if book_id is None:
            return {'message': 'Missing book_id in request payload'}, 400

        # Check if the user exists
        if not user:
            return {'message': 'User not found'}, 404

        # Check if the book exists
        book = Book.query.get(book_id)
        if not book:
            return {'message': 'Book not found'}, 404

        # Check if the cart item already exists for the user and book
        existing_cart_item = Cart.query.filter_by(user_id=user.id, book_id=book_id).first()
        if existing_cart_item:
            # If the cart item already exists, just return it (don't update quantity)
            # User can add the same book multiple times as separate cart items if needed
            return existing_cart_item, 200
        else:
            # If the cart item doesn't exist, create a new one
            cart = Cart(
                user_id=user.id,
                book_id=book_id,
                quantity=quantity
            )
            db.session.add(cart)
            db.session.commit()
            return cart, 201
        
@ns_events.route('/cart/<int:id>')
class EventAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_with(cart_model)
    def get(self, id):
        cart = Cart.query.get(id)
        if not cart:
            abort(404, message="Cart item not found")
        return cart, 200

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(cart_model_input)
    @ns_events.marshal_with(cart_model)
    def post(self, id):
        cart_data = ns_events.payload
        cart = Cart.query.get(id)
        if not cart:
            abort(404, message="Cart item not found")
    
    # Update the cart item with the provided data
        cart.user_id = cart_data.get("user_id", cart.user_id)
        cart.book_id = cart_data.get("book_id", cart.book_id)
        cart.quantity = cart_data.get("quantity", cart.quantity)
    
    # Commit the changes to the database
        db.session.commit()
    
        return cart, 200

            
    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(cart_model_input)
    @ns_events.marshal_with(cart_model)
    def put(self, id):
        cart_data = ns_events.payload
        cart = Cart.query.get(id)
        if not cart:
            abort(404, message="Cart item not found")
        cart.user_id = cart_data.get("user_id", cart.user_id)
        cart.book_id = cart_data.get("book_id", cart.book_id)
        cart.quantity = cart_data.get("quantity", cart.quantity)
        db.session.commit()
        return cart, 200

    @ns_events.doc(security="jsonWebToken")
    def delete(self, id):
        cart = Cart.query.get(id)
        if not cart:
            abort(404, message="Cart item not found")
        db.session.delete(cart)
        db.session.commit()
        return {}, 204  
    
@ns_events.route('/payment')
class PaymentAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_list_with(payment_model)
    @jwt_required()
    def get(self):
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        # Get payments for the current user, ordered by most recent first
        payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
        return payments

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(payment_input_model)
    @ns_events.marshal_with(payment_model)
    @jwt_required()
    def post(self):
        payment_data = ns_events.payload
        
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        # Use user_id from JWT token, not from payload
        payment = Payment(
            user_id=user.id,
            book_id=payment_data["book_id"],
            price=payment_data["price"],
            card_number=payment_data["card_number"],
            card_holder_name=payment_data["card_holder_name"],
            expiration_date=payment_data["expiration_date"],
            cvv=payment_data["cvv"]
        )
        db.session.add(payment)
        db.session.commit()
        
        # Notify via websocket
        try:
            import websocket
            websocket.notify_new_payment(payment)
            websocket.notify_dashboard_update()
        except Exception as e:
            print(f"Error sending websocket notification: {str(e)}")
        
        return payment, 201

@ns_events.route('/payment/<int:id>')
class PaymentDetailAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_with(payment_model)
    @jwt_required()
    def get(self, id):
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        payment = Payment.query.filter_by(id=id, user_id=user.id).first()
        if not payment:
            abort(404, message="Payment not found")
        return payment

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(payment_input_model)
    @ns_events.marshal_with(payment_model)
    @jwt_required()
    def put(self, id):
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        payment_data = ns_events.payload
        payment = Payment.query.filter_by(id=id, user_id=user.id).first()
        if not payment:
            abort(404, message="Payment not found")
        
        # Don't allow changing user_id
        payment.book_id = payment_data.get("book_id", payment.book_id)
        payment.price = payment_data.get("price", payment.price)
        payment.card_number = payment_data.get("card_number", payment.card_number)
        payment.card_holder_name = payment_data.get("card_holder_name", payment.card_holder_name)
        payment.expiration_date = payment_data.get("expiration_date", payment.expiration_date)
        payment.cvv = payment_data.get("cvv", payment.cvv)
        db.session.commit()
        return payment

    @ns_events.doc(security="jsonWebToken")
    @jwt_required()
    def delete(self, id):
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        payment = Payment.query.filter_by(id=id, user_id=user.id).first()
        if not payment:
            abort(404, message="Payment not found")
        db.session.delete(payment)
        db.session.commit()
        return {}, 204

@ns_events.route('/checkout')
class CheckoutAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(checkout_input_model)
    @ns_events.marshal_with(checkout_response_model)
    @jwt_required()
    def post(self):
        """
        Checkout multiple books from cart. 
        Creates payments for each book, adds books to UserBook, and clears cart items.
        """
        checkout_data = ns_events.payload
        
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            return {'message': 'User not found'}, 404
        
        # Get cart items to checkout
        cart_ids = checkout_data.get('cart_ids', [])
        
        if cart_ids:
            # Checkout specific cart items
            cart_items = Cart.query.filter(
                Cart.id.in_(cart_ids),
                Cart.user_id == user.id
            ).all()
        else:
            # Checkout all cart items for the user
            cart_items = Cart.query.filter_by(user_id=user.id).all()
        
        if not cart_items:
            return {'message': 'No items in cart to checkout'}, 400
        
        # Payment details
        card_number = checkout_data.get('card_number')
        card_holder_name = checkout_data.get('card_holder_name')
        expiration_date = checkout_data.get('expiration_date')
        cvv = checkout_data.get('cvv')
        
        if not all([card_number, card_holder_name, expiration_date, cvv]):
            return {'message': 'Missing payment details'}, 400
        
        payments = []
        total_amount = 0.0
        books_added_count = 0
        
        try:
            for cart_item in cart_items:
                book = Book.query.get(cart_item.book_id)
                if not book:
                    continue
                
                # Convert price string to float
                try:
                    price = float(book.price)
                except (ValueError, TypeError):
                    price = 0.0
                
                # Check if user already owns this book
                existing_userbook = UserBook.query.filter_by(
                    user_id=user.id,
                    book_id=book.id
                ).first()
                
                if existing_userbook:
                    # Skip if user already owns the book, but still remove from cart
                    db.session.delete(cart_item)
                    continue
                
                # Create payment record
                payment = Payment(
                    user_id=user.id,
                    book_id=book.id,
                    price=price,
                    card_number=card_number,
                    card_holder_name=card_holder_name,
                    expiration_date=expiration_date,
                    cvv=cvv
                )
                db.session.add(payment)
                # Flush to get payment ID before adding to list
                db.session.flush()
                payments.append(payment)
                total_amount += price
                
                # Add book to UserBook
                userbook = UserBook(
                    user_id=user.id,
                    book_id=book.id
                )
                db.session.add(userbook)
                books_added_count += 1
                
                # Remove cart item
                db.session.delete(cart_item)
            
            # Commit all changes at once
            db.session.commit()
            
            # Notify via websocket for each payment
            try:
                import websocket
                for payment in payments:
                    websocket.notify_new_payment(payment)
                websocket.notify_dashboard_update()
            except Exception as e:
                print(f"Error sending websocket notification: {str(e)}")
            
            return {
                'message': f'Successfully checked out {books_added_count} book(s)',
                'payments': payments,
                'total_amount': total_amount,
                'books_added': books_added_count
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error during checkout: {str(e)}'}, 500
    
@ns_events.route('/userbook')
class UserBookAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_with(userbook_model)
    @jwt_required()
    def get(self):
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        if not user:
            abort(404, message="User not found")

        userbooks = UserBook.query.filter_by(user_id=user.id).all()
        if not userbooks:
            abort(404, message="No UserBook entries found for the user")

        return userbooks

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(userbook_model_input)
    @ns_events.marshal_with(userbook_model)
    @jwt_required()
    def post(self):
        userbook_data = ns_events.payload

        # Extract username from JWT token
        current_username = get_jwt_identity()

        # Get user object from the database
        user = User.query.filter_by(username=current_username).first()

        # Extract book_id from the payload
        book_id = userbook_data.get('book_id')

        # Check if book_id is present
        if book_id is None:
            return {'message': 'Missing book_id in request payload'}, 400

        # Check if the user exists
        if not user:
            return {'message': 'User not found'}, 404

        # Check if the user already has the book in their userbook entries
        existing_userbook = UserBook.query.filter_by(user_id=user.id, book_id=book_id).first()
        if existing_userbook:
            return {'message': 'User already has this book in their userbook entries'}, 400

        # Create a new userbook entry
        userbook = UserBook(
            user_id=user.id,
            book_id=book_id
        )
        db.session.add(userbook)
        db.session.commit()

        return userbook, 200
    
@ns_events.route('/userbook/<int:id>')
class UserBookDetailAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    def delete(self, id):
        userbook = UserBook.query.get(id)
        if not userbook:
            abort(404, message="UserBook entry not found")
        db.session.delete(userbook)
        db.session.commit()
        return {}, 204

@ns_events.route('/rating')
class RatingAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_list_with(rating_model)
    @jwt_required()
    def get(self):
        """Get all ratings for a book or all ratings by current user"""
        book_id = ns_events.payload.get('book_id') if hasattr(ns_events, 'payload') else None
        
        if book_id:
            ratings = BookRating.query.filter_by(book_id=book_id).order_by(BookRating.created_at.desc()).all()
        else:
            # Get current user's ratings
            current_username = get_jwt_identity()
            user = User.query.filter_by(username=current_username).first()
            if not user:
                abort(404, message="User not found")
            ratings = BookRating.query.filter_by(user_id=user.id).order_by(BookRating.created_at.desc()).all()
        
        return ratings, 200

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(rating_input_model)
    @ns_events.marshal_with(rating_model)
    @jwt_required()
    def post(self):
        """Create or update a rating for a book"""
        rating_data = ns_events.payload
        
        # Extract username from JWT token
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        book_id = rating_data.get('book_id')
        rating_value = rating_data.get('rating')
        comment = rating_data.get('comment', '')
        
        # Validate rating
        if not book_id or not rating_value:
            return {'message': 'Missing book_id or rating'}, 400
        
        if rating_value < 1 or rating_value > 5:
            return {'message': 'Rating must be between 1 and 5'}, 400
        
        # Check if book exists
        book = Book.query.get(book_id)
        if not book:
            abort(404, message="Book not found")
        
        # Check if user already rated this book
        existing_rating = BookRating.query.filter_by(user_id=user.id, book_id=book_id).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_value
            existing_rating.comment = comment
            existing_rating.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Notify via websocket
            try:
                import websocket
                websocket.notify_new_rating(existing_rating)
                websocket.notify_dashboard_update()
            except Exception as e:
                print(f"Error sending websocket notification: {str(e)}")
            
            return existing_rating, 200
        else:
            # Create new rating
            rating = BookRating(
                user_id=user.id,
                book_id=book_id,
                rating=rating_value,
                comment=comment
            )
            db.session.add(rating)
            db.session.commit()
            
            # Notify via websocket
            try:
                import websocket
                websocket.notify_new_rating(rating)
                websocket.notify_dashboard_update()
            except Exception as e:
                print(f"Error sending websocket notification: {str(e)}")
            
            return rating, 201

@ns_events.route('/rating/<int:id>')
class RatingDetailAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_with(rating_model)
    @jwt_required()
    def get(self, id):
        rating = BookRating.query.get(id)
        if not rating:
            abort(404, message="Rating not found")
        return rating, 200

    @ns_events.doc(security="jsonWebToken")
    @ns_events.expect(rating_input_model)
    @ns_events.marshal_with(rating_model)
    @jwt_required()
    def put(self, id):
        """Update rating - only by the user who created it"""
        rating_data = ns_events.payload
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        rating = BookRating.query.get(id)
        if not rating:
            abort(404, message="Rating not found")
        
        # Check if user owns this rating
        if rating.user_id != user.id:
            abort(403, message="You can only update your own ratings")
        
        rating.rating = rating_data.get('rating', rating.rating)
        rating.comment = rating_data.get('comment', rating.comment)
        rating.updated_at = datetime.utcnow()
        
        db.session.commit()
        return rating, 200

    @ns_events.doc(security="jsonWebToken")
    @jwt_required()
    def delete(self, id):
        """Delete rating - only by the user who created it"""
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        rating = BookRating.query.get(id)
        if not rating:
            abort(404, message="Rating not found")
        
        # Check if user owns this rating or is admin
        if rating.user_id != user.id and user.role != 'admin':
            abort(403, message="You can only delete your own ratings")
        
        db.session.delete(rating)
        db.session.commit()
        return {}, 204

@ns_events.route('/book/<int:book_id>/ratings')
class BookRatingsAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_list_with(rating_model)
    def get(self, book_id):
        """Get all ratings for a specific book"""
        book = Book.query.get(book_id)
        if not book:
            abort(404, message="Book not found")
        
        ratings = BookRating.query.filter_by(book_id=book_id).order_by(BookRating.created_at.desc()).all()
        
        # Calculate average rating
        if ratings:
            avg_rating = sum(r.rating for r in ratings) / len(ratings)
            return {
                'ratings': ratings,
                'average_rating': round(avg_rating, 2),
                'total_ratings': len(ratings)
            }, 200
        else:
            return {
                'ratings': [],
                'average_rating': 0,
                'total_ratings': 0
            }, 200

@ns_events.route('/author/my-books/buyers')
class AuthorBookBuyersAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_list_with(book_buyers_model)
    @api_author_or_admin_required
    @jwt_required()
    def get(self):
        """Get all buyers/subscribers for author's books"""
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        # Get author profile
        author = Author.query.filter_by(user_id=user.id).first()
        if not author and user.role != 'admin':
            abort(403, message="You are not an author")
        
        # Get all books by this author (or all books if admin)
        if user.role == 'admin':
            books = Book.query.all()
        else:
            books = Book.query.filter_by(author_id=author.id).all()
        
        result = []
        for book in books:
            # Get all users who bought this book
            payments = Payment.query.filter_by(book_id=book.id).all()
            userbooks = UserBook.query.filter_by(book_id=book.id).all()
            
            # Combine unique buyers
            buyer_ids = set()
            buyers_list = []
            total_revenue = 0.0
            
            for payment in payments:
                if payment.user_id not in buyer_ids:
                    buyer_ids.add(payment.user_id)
                    buyer_user = User.query.get(payment.user_id)
                    if buyer_user:
                        buyers_list.append(buyer_user)
                total_revenue += float(payment.price)
            
            for userbook in userbooks:
                if userbook.user_id not in buyer_ids:
                    buyer_ids.add(userbook.user_id)
                    buyer_user = User.query.get(userbook.user_id)
                    if buyer_user:
                        buyers_list.append(buyer_user)
            
            result.append({
                'book_id': book.id,
                'book_title': book.title,
                'buyers': buyers_list,
                'total_buyers': len(buyers_list),
                'total_revenue': total_revenue
            })
        
        return result, 200

@ns_events.route('/author/my-books/<int:book_id>/buyers')
class AuthorBookBuyersDetailAPI(Resource):
    @ns_events.doc(security="jsonWebToken")
    @ns_events.marshal_with(book_buyers_model)
    @api_author_or_admin_required
    @jwt_required()
    def get(self, book_id):
        """Get buyers for a specific book"""
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        
        if not user:
            abort(404, message="User not found")
        
        book = Book.query.get(book_id)
        if not book:
            abort(404, message="Book not found")
        
        # Check if user is the author or admin
        if user.role != 'admin':
            author = Author.query.filter_by(user_id=user.id).first()
            if not author or book.author_id != author.id:
                abort(403, message="You can only view buyers for your own books")
        
        # Get all users who bought this book
        payments = Payment.query.filter_by(book_id=book_id).all()
        userbooks = UserBook.query.filter_by(book_id=book_id).all()
        
        buyer_ids = set()
        buyers_list = []
        total_revenue = 0.0
        
        for payment in payments:
            if payment.user_id not in buyer_ids:
                buyer_ids.add(payment.user_id)
                buyer_user = User.query.get(payment.user_id)
                if buyer_user:
                    buyers_list.append(buyer_user)
            total_revenue += float(payment.price)
        
        for userbook in userbooks:
            if userbook.user_id not in buyer_ids:
                buyer_ids.add(userbook.user_id)
                buyer_user = User.query.get(userbook.user_id)
                if buyer_user:
                    buyers_list.append(buyer_user)
        
        return {
            'book_id': book.id,
            'book_title': book.title,
            'buyers': buyers_list,
            'total_buyers': len(buyers_list),
            'total_revenue': total_revenue
        }, 200
