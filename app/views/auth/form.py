from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DecimalField
from wtforms.validators import DataRequired
from wtforms.widgets import PasswordInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
from app.models import Author, Category


class LoginForm(FlaskForm):
    username = StringField('Username', [DataRequired()], render_kw={'placeholder': 'username'})
    email = StringField('Email', [DataRequired()], render_kw={'placeholder': 'email'})
    password = PasswordField('Password', widget=PasswordInput(hide_value=True), validators=[DataRequired()], render_kw={'placeholder': 'password'})
    gender = StringField('Gender', [DataRequired()], render_kw={'placeholder': 'gender'})
    remember = BooleanField('Remember me')
    submit_login = SubmitField('Login')
    
class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()], render_kw={'placeholder': 'Enter category'})
    submit = SubmitField('Submit')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={'placeholder': 'Enter username'})
    email = StringField('Email', validators=[DataRequired()], render_kw={'placeholder': 'Enter email'})
    password = PasswordField('Password', widget=PasswordInput(hide_value=True), render_kw={'placeholder': 'Enter password (optional)'})
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()], render_kw={'placeholder': 'Enter role'})
    profile_image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

    submit = SubmitField('Submit')
    
class AuthorForm(FlaskForm):
    author_name = StringField('Author Name', validators=[DataRequired()], render_kw={'placeholder': 'Enter author name'})
    author_decs = TextAreaField('Author Description', validators=[DataRequired()], render_kw={'placeholder': 'Enter author description'})
    gender = StringField('Gender', validators=[DataRequired()], render_kw={'placeholder': 'Enter gender'})
    author_image = FileField('Author Image', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()], places=2)
    publisher = StringField('Publisher', validators=[DataRequired()])
    author = SelectField('Author', coerce=int, validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Upload Book Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    file = FileField('Upload Book File (PDF)', validators=[FileAllowed(['pdf'])]) 
    submit = SubmitField('Add Book')

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        user = kwargs.pop('user', None)
        super(BookForm, self).__init__(*args, **kwargs)
        
        # Populate choices for author field based on user role
        if user and user.role == 'author':
            # Authors can only select themselves
            author_profile = Author.query.filter_by(user_id=user.id).first()
            if author_profile:
                self.author.choices = [(author_profile.id, author_profile.author_name)]
            else:
                self.author.choices = []
        else:
            # Admins can select any author
            self.author.choices = [(author.id, author.author_name) for author in Author.query.all()]
        
        # Populate choices for category field
        self.category.choices = [(category.id, category.name) for category in Category.query.all()]