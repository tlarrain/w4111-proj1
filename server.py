
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from flask import Flask, request, flash, render_template, g, redirect, Response
from forms import LoginForm, SearchForm

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'
DATABASEURI = "postgresql://tal2150:7764@35.243.220.243/proj1part2"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback
    traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        s = text("SELECT * FROM Users U WHERE U.user_name = :username AND U.password = :password")
        cursor = g.conn.execute(s, username=form.username.data, password=form.password.data)
        names = []
        if cursor.rowcount == 1:
          return redirect('/')
        cursor.close()
    return render_template('login.html', title='Sign In', form=form)

@app.route('/', methods=['GET', 'POST'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  search_form = SearchForm()
  if search_form.validate_on_submit():
    return search_results(search_form.searchTerms.data)
  return render_template('index.html', title='Home', search_form=search_form)


@app.route('/results')
def search_results(search):
  string_match = '%' + search.replace(' ', '%%') + '%'
  s = text("""
      WITH FullTable AS
      (SELECT P.purl, P.title, P.model, R.programming_language, K.keyword, A.first_name,
      A.last_name, I.type, I.name, I.country, I.city 
      FROM Papers P 
      LEFT OUTER JOIN Published_On PO ON P.purl = PO.purl
      LEFT OUTER JOIN Repositories R ON PO.url = R.url
      LEFT OUTER JOIN Is_Related_To IRT ON PO.purl = IRT.purl
      LEFT OUTER JOIN Keywords K ON IRT.keyword = K.keyword  
      LEFT OUTER JOIN Published_By PB ON P.purl = PB.purl 
      LEFT OUTER JOIN Authors A ON PB.aid = A.aid
      LEFT OUTER JOIN Works_At WA ON WA.aid = A.aid
      LEFT OUTER JOIN Institutions I ON I.iid = WA.iid)
      SELECT DISTINCT FT.title
      FROM FullTable FT 
      WHERE 
      FT.title LIKE :string_match OR
      FT.model LIKE :string_match  OR
      FT.programming_language LIKE :string_match OR
      FT.keyword LIKE :string_match OR 
      FT.first_name LIKE :string_match OR
      FT.last_name LIKE :string_match OR
      FT.name LIKE :string_match OR
      FT.type LIKE :string_match OR
      FT.country LIKE :string_match OR
      FT.city LIKE :string_match; 
          """)
  cursor = g.conn.execute(s, string_match=string_match)
  results = list(cursor.fetchall())
  return render_template('results.html', results=results)


@app.route('/advanced')
def advanced():
    return render_template('advanced.html')

@app.route('/advanced/search')
def adv_search():
    return render_template('advancedsearch.html')

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')

def convert_string_to_query_array(string):
  return str(string.split(' ')).replace('[', '(').replace(']', ')')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
