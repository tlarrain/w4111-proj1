
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
from forms import LoginForm, SearchForm
import datetime
import utils

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config['SECRET_KEY'] = 'you-will-never-guess'
DATABASEURI = "postgresql://tal2150:7764@35.243.220.243/proj1part2"
engine = create_engine(DATABASEURI)

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
    USER = {}
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
      SELECT  PB.aid, A.first_name, A.last_name, I.iid, I.name
      FROM Papers P RIGHT OUTER JOIN Published_by PB ON P.purl = PB.purl
      INNER JOIN Authors A ON PB.aid = A.aid
      INNER JOIN Works_At WA ON WA.aid = A.aid
      INNER JOIN Institutions I ON I.iid = WA.iid
      WHERE P.purl = :purl;
    """)
  cursor = g.conn.execute(s, purl=purl)
  authors = list(cursor.fetchall())
  cursor.close()
  return render_template('paper_details.html', paper=paper, authors=authors)


def store_history(purl):
  global USER
  if not USER:
    return
  today = datetime.datetime.now().date()
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


@app.route('/institutions', methods=['GET', 'POST'])
def institutions():
  query = """
    SELECT *
    FROM Institutions I
  """
  institutions_cursor = g.conn.execute(query)
  institutions = []
  for i in institutions_cursor:
    institutions.append(i)
  return render_template('institutions.html', institutions=institutions)


@app.route('/institution/<iid>', methods=['GET', 'POST'])
def institution_detail(iid):
  i_query = text("""
  SELECT *
  FROM Institutions I
  WHERE I.iid = :iid
  """)
  institution_cursor = g.conn.execute(i_query, iid=iid)
  details = institution_cursor.fetchone()
  a_query = text("""
      SELECT A.aid, A.first_name, A.last_name
      FROM Authors A
      INNER JOIN Works_At WA ON WA.aid = A.aid
      INNER JOIN Institutions I ON I.iid = WA.iid
      WHERE I.iid = :iid
      ORDER BY A.last_name
      """)
  authors_cursor = g.conn.execute(a_query, iid=iid)
  authors = authors_cursor.fetchall()
  p_query = text("""
      SELECT DISTINCT P.title, P.purl, P.number_of_citations
      FROM Papers P
      INNER JOIN Published_By PB ON PB.purl = P.purl
      INNER JOIN Authors A ON PB.aid = A.aid
      INNER JOIN Works_At WA ON WA.aid = A.aid
      INNER JOIN Institutions I ON I.iid = WA.iid
      WHERE I.iid = :iid
      ORDER BY P.number_of_citations DESC
      """)
  p_cursor = g.conn.execute(p_query, iid=iid)
  papers = []
  for p in p_cursor:
    papers.append({'title': p.title, 'purl': utils.encode_url(p.purl), 'citations': p.number_of_citations})
  context = {'details': details, 'authors': authors, 'papers': papers}
  institution_cursor.close()
  authors_cursor.close()
  p_cursor.close()
  return render_template('institution_details.html', **context)


@app.route('/author/<aid>', methods=['GET', 'POST'])
def author_detail(aid):
  i_query = text("""
  SELECT A.first_name, A.last_name, I.name as inst_name, I.iid
  FROM Authors A INNER JOIN Works_At WA ON WA.aid = A.aid
  INNER JOIN Institutions I ON I.iid = WA.iid
  WHERE A.aid = :aid
  """)
  p_query = text("""
  SELECT DISTINCT P.purl, P.title, P.number_of_citations
  FROM Authors A INNER JOIN Published_By PB ON A.aid = PB.aid
  INNER JOIN Papers P ON P.purl = PB.purl
  WHERE A.aid = :aid
  """)
  cursor = g.conn.execute(i_query, aid=aid)
  details = cursor.fetchone()
  cursor = g.conn.execute(p_query, aid=aid)
  papers = []
  for p in cursor:
    new_p = {'purl': utils.encode_url(p.purl), 'title': p.title, 'citations': p.number_of_citations}
    papers.append(new_p)
  context = {'author': details, 'papers': papers}
  return render_template('author_details.html', **context)


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
