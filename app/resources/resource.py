from flask_restx import Resource, Namespace, abort
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app.resources.api_models import *
from app.models import *
from app.extensions import db
from app.authorize import authorizations
from werkzeug.security import generate_password_hash
from cloudinary_service import upload_image, upload_pdf

ns_profile = Namespace('profile', authorizations=authorizations)
ns_author = Namespace('author', authorizations=authorizations)
ns_category = Namespace('category', description='Category operations', authorizations=authorizations)
ns_book = Namespace('books', description='Book operations', authorizations=authorizations)

ns_profile.decorators = [jwt_required()]
ns_author.decorators = [jwt_required()]
ns_category.decorators = [jwt_required()]
ns_book.decorators = [jwt_required()]

# Input profile
@ns_profile.route('/profile')
class ProfileAPIList(Resource):
    @ns_profile.doc(security="jsonWebToken")
    @ns_profile.marshal_list_with(profile_model)
    def get(self):
        try:
            profiles = Profile.query.all()
            return profiles
        except Exception as e:
            return abort(500, message=f"Error fetching profiles: {str(e)}")

    @ns_profile.doc(security="jsonWebToken")
    @ns_profile.expect(profile_input_model)
    @ns_profile.marshal_with(profile_model)
    def post(self):
        try:
            data = ns_profile.payload
            # Check if username already exists
            existing_profile = Profile.query.filter_by(username=data["username"]).first()
            if existing_profile:
                return abort(400, message="Username already exists.")
            
            profile = Profile(
                username=data["username"],
                email=data["email"],
                password_hash=generate_password_hash(data.get("password", "default_password")),
                gender=data.get("gender", "Other"),  
                role=data.get("role", "user"),
                profile_image=data.get("profile_image", None)
            )
            db.session.add(profile)
            db.session.commit()
            return profile, 201
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error creating profile: {str(e)}")

# Update and delete search profile by id
@ns_profile.route('/profile/<int:id>')
class ProfileAPI(Resource):
    @ns_profile.doc(security="jsonWebToken")
    @ns_profile.marshal_with(profile_model)
    def get(self, id):
        try:
            profile = Profile.query.get(id)
            if profile is None:
                return abort(404, message="Profile not found.")
            return profile
        except Exception as e:
            return abort(500, message=f"Error fetching profile: {str(e)}")

    @ns_profile.doc(security="jsonWebToken")
    @ns_profile.expect(profile_input_model)
    @ns_profile.marshal_with(profile_model)
    def put(self, id):
        try:
            data = ns_profile.payload
            profile = Profile.query.get(id)

            if profile is None:
                return abort(404, message="Profile not found.")

            # Validate 'gender' field if provided
            valid_genders = ["male", "female", "Other"]
            if "gender" in data and data["gender"] not in valid_genders:
                return abort(400, message="Invalid value for 'gender'. Allowed values are 'male', 'female', or 'Other'.")

            # Update profile fields
            profile.username = data.get("username", profile.username)
            profile.email = data.get("email", profile.email)
            profile.gender = data.get("gender", profile.gender)
            profile.role = data.get("role", profile.role)
            profile.profile_image = data.get("profile_image", profile.profile_image)

            db.session.commit()
            return profile
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error updating profile: {str(e)}")

    @ns_profile.doc(security="jsonWebToken")
    def delete(self, id):
        try:
            profile = Profile.query.get(id)
            if profile is None:
                return abort(404, message="Profile not found.")

            db.session.delete(profile)
            db.session.commit()
            return {}, 204
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error deleting profile: {str(e)}")

@ns_book.route("/category")
class CategoryAPIList(Resource):
    @ns_book.doc(security="jsonWebToken")
    @ns_book.marshal_list_with(category_model)
    def get(self):
        try:
            return Category.query.all()
        except Exception as e:
            return abort(500, message=f"Error fetching categories: {str(e)}")

    @ns_book.doc(security="jsonWebToken")
    @ns_book.expect(category_input_model)
    @ns_book.marshal_with(category_model)
    def post(self):
        try:
            data = ns_book.payload
            # Check if category name already exists
            existing_category = Category.query.filter_by(name=data["name"]).first()
            if existing_category:
                return abort(400, message="Category name already exists.")
            
            category = Category(name=data["name"])
            db.session.add(category)
            db.session.commit()
            return category, 201
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error creating category: {str(e)}")

# Update and delete category by id
@ns_book.route('/category/<int:id>') 
class CategoryAPI(Resource):
    @ns_book.doc(security="jsonWebToken")
    @ns_book.marshal_with(category_model)
    def get(self, id):
        try:
            category = Category.query.get(id)
            if category is None:
                return abort(404, message="Category not found.")
            return category
        except Exception as e:
            return abort(500, message=f"Error fetching category: {str(e)}")
    
    @ns_book.doc(security="jsonWebToken")
    @ns_book.expect(category_input_model)
    @ns_book.marshal_with(category_model)
    def put(self, id):
        try:
            data = ns_book.payload
            category = Category.query.get(id)

            if category is None:
                return abort(404, message="Category not found.")
            
            category.name = data.get("name", category.name)

            db.session.commit()
            return category
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error updating category: {str(e)}")
    
    @ns_book.doc(security="jsonWebToken")
    def delete(self, id):
        try:
            category = Category.query.get(id)
            if category is None:
                return abort(404, message="Category not found.")

            db.session.delete(category)
            db.session.commit()
            return {}, 204
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error deleting category: {str(e)}")

@ns_author.route('/author')
class AuthorAPIList(Resource):
    @ns_author.doc(security="jsonWebToken")
    @ns_author.marshal_list_with(author_model)
    def get(self):
        try:
            return Author.query.all()
        except Exception as e:
            return abort(500, message=f"Error fetching authors: {str(e)}")
    
    @ns_author.doc(security="jsonWebToken")
    @ns_author.expect(author_input_model)
    @ns_author.marshal_with(author_model)
    def post(self):
        try:
            data = ns_author.payload
            # Check if author name already exists
            existing_author = Author.query.filter_by(author_name=data["author_name"]).first()
            if existing_author:
                return abort(400, message="Author name already exists.")
            
            author = Author(
                author_name=data["author_name"],
                author_decs=data["author_decs"],
                gender=data.get("gender", "Other"),
                author_image=data.get("author_image", None)
            )
            db.session.add(author)
            db.session.commit()
            return author, 201
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error creating author: {str(e)}")

# Define update and delete author by ID endpoint
@ns_author.route('/author/<int:id>')
class AuthorAPI(Resource):
    @ns_author.doc(security="jsonWebToken")
    @ns_author.marshal_with(author_model)
    def get(self, id):
        try:
            author = Author.query.get(id)
            if author is None:
                return abort(404, message="Author not found.")
            return author
        except Exception as e:
            return abort(500, message=f"Error fetching author: {str(e)}")

    @ns_author.doc(security="jsonWebToken")
    @ns_author.expect(author_input_model)
    @ns_author.marshal_with(author_model)
    def put(self, id):
        try:
            data = ns_author.payload
            author = Author.query.get(id)

            if author is None:
                return abort(404, message="Author not found.")

            author.author_name = data.get("author_name", author.author_name)
            author.author_decs = data.get("author_decs", author.author_decs)
            author.gender = data.get("gender", author.gender)
            author.author_image = data.get("author_image", author.author_image)

            db.session.commit()
            return author
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error updating author: {str(e)}")

    @ns_author.doc(security="jsonWebToken")
    def delete(self, id):
        try:
            author = Author.query.get(id)
            if author is None:
                return abort(404, message="Author not found.")

            db.session.delete(author)
            db.session.commit()
            return {}, 204
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error deleting author: {str(e)}")
    
@ns_book.route("/book")
class BookResource(Resource):
    @ns_book.doc(security="jsonWebToken")
    @ns_book.marshal_list_with(book_model)
    def get(self):
        try:
            books = Book.query.all()
            return books
        except Exception as e:
            return abort(500, message=f"Error fetching books: {str(e)}")

    @ns_book.doc(security="jsonWebToken")
    @ns_book.expect(book_input_model)
    @ns_book.marshal_with(book_model)
    def post(self):
        try:
            data = ns_book.payload

            # Check if the provided author_id exists
            author = Author.query.get(data["author_id"])
            if author is None:
                return abort(400, message="Author not found.")

            # Check if the provided category_id exists
            category = Category.query.get(data["category_id"])
            if category is None:
                return abort(400, message="Category not found.")

            # Upload image to Cloudinary if available
            image_url = None
            if 'image_file' in data:
                try:
                    image_file = data['image_file']
                    upload_result = upload_image(image_file)
                    image_url = upload_result['secure_url']
                except Exception as e:
                    return abort(500, message=f"Error uploading image: {str(e)}")

            # Upload PDF to Cloudinary if available
            pdf_url = None
            if 'pdf_file' in data:
                try:
                    pdf_file = data['pdf_file']
                    upload_result = upload_pdf(pdf_file)
                    pdf_url = upload_result['secure_url']
                except Exception as e:
                    return abort(500, message=f"Error uploading PDF: {str(e)}")

            # Create a new book with the specified author, category, image, and pdf
            book = Book(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                publisher=data['publisher'],
                category_id=data["category_id"],
                author_id=data["author_id"],
                book_image=image_url,
                book_pdf=pdf_url,
            )

            db.session.add(book)
            db.session.commit()

            return book, 201
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error creating book: {str(e)}")

@ns_book.route('/book/<string:title>')
class BookSearch(Resource):
    @ns_book.doc(security= "jsonWebToken")
    @ns_book.marshal_list_with(book_model)
    def get(self, title):
        try:
            # Perform a case-insensitive search for books by title
            books = Book.query.filter(func.lower(Book.title) == func.lower(title)).all()
            
            if not books:
                return abort(404, message="No books found with the given title.")
            
            return books
        except Exception as e:
            return abort(500, message=f"Error searching books: {str(e)}")

@ns_book.route('/book/<int:id>')
class BookAPI(Resource):
    @ns_book.doc(security="jsonWebToken")
    @ns_book.marshal_with(book_model)
    def get(self, id):
        try:
            # Retrieve the book by its ID and load its related author and category information
            book = Book.query.options(db.joinedload(Book.author), db.joinedload(Book.category)).get(id)
            if book is None:
                return abort(404, message="Book not found.")
            return book
        except Exception as e:
            return abort(500, message=f"Error fetching book: {str(e)}")
    
    @ns_book.doc(security="jsonWebToken")
    @ns_book.expect(book_input_model)
    @ns_book.marshal_with(book_model)  
    def put(self, id):
        try:
            data = ns_book.payload
            book = Book.query.get(id)

            if book is None:
                return abort(404, message="Book not found.")

            # Check if the provided author_id exists
            author = Author.query.get(data["author_id"])
            if author is None:
                return abort(400, message="Author not found.")

            # Check if the provided category_id exists
            category = Category.query.get(data["category_id"])
            if category is None:
                return abort(400, message="Category not found.")

            # Update book fields
            book.title = data.get("title", book.title)
            book.description = data.get("description", book.description)
            book.price = data.get("price", book.price)
            book.publisher = data.get("publisher", book.publisher)
            book.category_id = data.get("category_id", book.category_id)
            book.author_id = data.get("author_id", book.author_id)

            # Update image if available
            if 'image_file' in data:
                try:
                    image_file = data['image_file']
                    upload_result = upload_image(image_file)
                    book.book_image = upload_result['secure_url']
                except Exception as e:
                    return abort(500, message=f"Error uploading image: {str(e)}")

            # Update PDF if available
            if 'pdf_file' in data:
                try:
                    pdf_file = data['pdf_file']
                    upload_result = upload_pdf(pdf_file)
                    book.book_pdf = upload_result['secure_url']
                except Exception as e:
                    return abort(500, message=f"Error uploading PDF: {str(e)}")

            db.session.commit()
            return book
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error updating book: {str(e)}")

    @ns_book.doc(security="jsonWebToken")
    def delete(self, id):
        try:
            book = Book.query.get(id)
            if book is None:
                return abort(404, message="Book not found.")

            db.session.delete(book)
            db.session.commit()
            return {}, 204
        except Exception as e:
            db.session.rollback()
            return abort(500, message=f"Error deleting book: {str(e)}")


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt','png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Assuming you have defined the ImageModel in your models

# @ns_book.route('/image')
# class ImageResource(Resource):
#     @ns_book.doc(security="jsonWebToken")
#     @ns_book.expect(image_input_model)
#     @ns_book.marshal_with(image_model)
#     def post(self):
#         try:
#             file = request.files['file']

#             if 'file' not in request.files:
#                 return abort(400, message="No file part")
#             if file.filename == '':
#                 return abort(400, message="No selected file")

#             if file and allowed_file(file.filename):
#                 cloudinary_response = upload(file)
#                 cloudinary_url = cloudinary_response['secure_url']

#                 image = ImageModel(file_path=cloudinary_url)
#                 db.session.add(image)
#                 db.session.commit()

#                 return {"message": "Image uploaded successfully", "file_path": cloudinary_url}, 201

#             return abort(400, message="Invalid file extension")
#         except Exception as e:
#             return abort(500, message="Error uploading the image: {}".format(str(e)))
        
#     @ns_book.doc(security="jsonWebToken")
#     @ns_book.marshal_with(image_model)
#     def get(self):
#         images = ImageModel.query.all()
#         return images

# @ns_book.route('/pdf')
# class PDFResource(Resource):
#     @ns_book.doc(security="jsonWebToken")
#     @ns_book.expect(pdf_input_model)
#     @ns_book.marshal_with(pdf_model)
#     def post(self):
#         try:
#             file = request.files['file']

#             if 'file' not in request.files:
#                 return abort(400, message="No file part")
#             if file.filename == '':
#                 return abort(400, message="No selected file")

#             if file and allowed_file(file.filename):
#                 cloudinary_response = upload(file)
#                 cloudinary_url = cloudinary_response['secure_url']

#                 pdf = PDFModel(file_path=cloudinary_url)
#                 db.session.add(pdf)
#                 db.session.commit()

#                 return {"message": "PDF uploaded successfully", "file_path": cloudinary_url}, 201

#             return abort(400, message="Invalid file extension")
#         except Exception as e:
#             return abort(500, message="Error uploading the PDF: {}".format(str(e)))
    
#     @ns_book.doc(security="jsonWebToken")
#     @ns_book.marshal_with(pdf_model)
#     def get(self):
#         pdfs = PDFModel.query.all()
#         return pdfs
