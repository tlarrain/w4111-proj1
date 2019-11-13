from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class SearchForm(FlaskForm):
    searchTerms = StringField('Type your search', validators=[DataRequired()])
    submit = SubmitField('Go!')


class AdvancedSearchForm(FlaskForm):
    title = StringField('Title', default='%_%')
    model = StringField('Model', default= '%_%')
    published_year = DateField('Published Year', validators=[Optional()], default= '%_%')
    minimum_citations = IntegerField('Minimum number of citations', default=0)
    repo_programming_language = StringField('Programming Language', default= '%_%')
    repo_published_year = DateField('Published Year', validators=[Optional()])
    keywords = StringField('Keywords', default= '%_%')
    author_first_name = StringField('First Name', default= '%_%')
    author_last_name = StringField('Last Name', default= '%_%')
    inst_name = StringField('Name', default= '%_%')
    inst_country = StringField('Country', default= '%_%')
    inst_city = StringField('City', default= '%_%')
    inst_zip = StringField('Zip', default= '%_%')
    inst_street = StringField('Street', default= '%_%')
    inst_street_no = StringField('Street Number', default= '%_%')
    inst_type = SelectField('Type', choices=[('all', 'all'), ('academic', 'academic'), ('non-academic', 'non-academic')], default= 'all')
    submit = SubmitField('Search', default= '%_%')

