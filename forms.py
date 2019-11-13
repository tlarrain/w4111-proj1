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
    title = StringField('Title')
    model = StringField('Model')
    published_year = IntegerField('Published Year', validators=[Optional()], default=1900)
    minimum_citations = IntegerField('Minimum number of citations', validators=[Optional()], default=0)
    repo_programming_language = StringField('Programming Language')
    repo_published_year = IntegerField('Published Year', validators=[Optional()], default=1900)
    keywords = StringField('Keywords')
    author_first_name = StringField('First Name')
    author_last_name = StringField('Last Name')
    inst_name = StringField('Name')
    inst_country = StringField('Country')
    inst_city = StringField('City')
    inst_zip = StringField('Zip')
    inst_street = StringField('Street')
    inst_street_no = StringField('Street Number')
    inst_type = SelectField('Type', choices=[('academic non-academic', 'all'), ('academic', 'academic'),
                                             ('non-academic', 'non-academic')])
    submit = SubmitField('Search')

