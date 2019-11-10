
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
from flask import Flask, render_template, g, redirect
from flask_login import LoginManager
from forms import LoginForm, SearchForm
import datetime
import utils

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'
DATABASEURI = "postgresql://tal2150:7764@35.243.220.243/proj1part2"
engine = create_engine(DATABASEURI)
login_manager = LoginManager()
login_manager.init_app(app)

USER = {}

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    global USER
    form = LoginForm()
    if form.validate_on_submit():
        s = text("SELECT * FROM Users U WHERE U.user_name = :username AND U.password = :password")
        cursor = g.conn.execute(s, username=form.username.data, password=form.password.data)
        names = []
        if cursor.rowcount == 1:
          USER = cursor.fetchone()
          return redirect('/')
        cursor.close()
    return render_template('login.html', title='Sign In', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
  global USER
  search_form = SearchForm()
  if search_form.validate_on_submit():
    return search_results(search_form.searchTerms.data)
  return render_template('index.html', title='Home', search_form=search_form, user=USER.first_name if USER else '')


@app.route('/results')
def search_results(search):
  s = text("""
      SELECT  P.title, P.purl
      FROM Papers P
      WHERE P.purl IN (
        SELECT I.purl
        FROM Is_Related_To I
        WHERE I.keyword in :keywords
      ); 
          """)
  cursor = g.conn.execute(s, keywords=tuple(search.split(' ')))
  results = []
  for result in cursor:
    result = {"title": result[0], "purl": utils.encode_url(result[1])}
    results.append(result)
  cursor.close()
  return render_template('results.html', results=results)


@app.route('/details/<purl>', methods=['GET', 'POST'])
def paper_details(purl):
  purl = utils.decode_url(purl)
  try:
    store_history(purl)
  except:
    pass
  s = text("""
        SELECT  P.title, P.purl, P.model, PO.url
        FROM Papers P LEFT OUTER JOIN Published_On PO ON P.purl = PO.purl
        WHERE P.purl = :purl;
      """)
  cursor = g.conn.execute(s, purl=purl)
  paper = cursor.fetchone()
  s = text("""
      SELECT  PB.aid, A.first_name, A.last_name, I.name
      FROM Papers P RIGHT OUTER JOIN Published_by PB ON P.purl = PB.purl
      INNER JOIN Authors A ON PB.aid = A.aid
      INNER JOIN Works_At WA ON WA.aid = A.aid
      INNER JOIN Institutions I ON I.iid = WA.iid
      WHERE P.purl = :purl;
    """)
  cursor = g.conn.execute(s, purl=purl)
  authors = []
  for c in cursor:
    authors.append(c)
  cursor.close()
  return render_template('details.html', paper=paper, authors=authors)


def store_history(purl):
  today = datetime.datetime.now().date()
  global USER
  get_query = text("""
  SELECT * FROM Have_Read HR
  WHERE HR.user_name = :user_name AND HR.purl = :purl AND HR.date = :date;
  """)
  get_cursor = g.conn.execute(get_query, user_name=USER.user_name, purl=purl, date=today)
  result = get_cursor.fetchone()
  if result:
    return
  insert_query = text("""
  INSERT INTO Have_Read(user_name, purl, date)
  VALUES (:user_name, :purl, :date);
  """)
  insert_cursor = g.conn.execute(insert_query, user_name=USER.user_name, purl=purl, date=today)
  insert_cursor.close()


@app.route('/my-account', methods=['GET', 'POST'])
def my_account():
  global USER
  if not USER:
      return redirect('/login')
  user_detail_query = text("""
  SELECT *
  FROM Users U
  WHERE U.user_name = :username;
  """)
  user_cursor = g.conn.execute(user_detail_query, username=USER.user_name)
  user = user_cursor.fetchone()
  history_query = text("""
  SELECT P.purl, P.title, HR.date
  FROM Have_Read HR INNER JOIN Papers P ON P.purl = HR.purl
  WHERE HR.user_name = :username
  ORDER BY HR.date DESC
  """)
  history_cursor = g.conn.execute(history_query, username=USER.user_name)
  history = []
  for h in history_cursor:
    h = {'title': h.title, 'purl': utils.encode_url(h.purl), 'date': h.date}
    history.append(h)
  context = {'user': user, 'history': history}
  return render_template("my-account.html", **context)


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
