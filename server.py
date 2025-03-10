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
from forms import LoginForm, SearchForm, AdvancedSearchForm, RegisterForm
import datetime
import utils
# from pprint import pprint


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


@app.route('/')
def default():
    return redirect('/home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global USER
    USER = {}
    form = LoginForm()
    if form.validate_on_submit():
        cursor = g.conn.execute(text("""SELECT * FROM Users U WHERE
        U.user_name = :username AND U.password = :password"""),
                                username=form.username.data, password=form.password.data)
        if cursor.rowcount == 1:
            USER = cursor.fetchone()
            return redirect('/home')
        cursor.close()
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    global USER
    form = RegisterForm()
    mandatory_error = False
    user_exists_error = False
    if form.validate_on_submit():
        user_created = create_user(form.username.data,
                                   form.password.data,
                                   form.first_name.data,
                                   form.last_name.data,
                                   form.date_of_birth.data.strftime('%Y-%m-%d'))
        if user_created:
            USER = {
                'user_name': form.username.data,
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'date_of_birth': form.date_of_birth.data.strftime('%Y-%m-%d')
            }
            return redirect('/home')
        else:
            user_exists_error = True
            form.username.data = ''
    else:
        mandatory_error = True
    context = {
      'form': form,
      'errors': {
        'user_exists': user_exists_error,
        'mandatory': mandatory_error,
      }
    }
    return render_template('register.html', **context)


def create_user(user_name, password, first_name, last_name, dob):
    user = g.conn.execute(text("SELECT user_name from Users U WHERE U.user_name = :user_name"),
                          user_name=user_name).fetchone()
    if user:
        return False
    g.conn.execute(text("""
  INSERT INTO Users (user_name, first_name, last_name, date_of_birth, password)
  VALUES (:user_name, :first_name, :last_name, :date_of_birth, :password);
  """), user_name=user_name, first_name=first_name, last_name=last_name, date_of_birth=dob, password=password)
    return True


@app.route('/home', methods=['GET', 'POST'])
def index():
    global USER
    search_form = SearchForm()
    recommendations = recommender()
    models = g.conn.execute("""
    SELECT DISTINCT P.model FROM Papers P;
    """).fetchall()
    applications = ['security', 'finance', 'medicine', 'recognition']
    context = {
        'title': 'Home',
        'search_form': search_form,
        'user': USER['first_name'] if USER else '',
        'recommendations': recommendations,
        'models': models,
        'applications': applications,
    }
    if search_form.validate_on_submit():
        return redirect('/results/' + utils.encode_url(search_form.searchTerms.data))
    return render_template('index.html', **context)


def search_term(search):
    string_match = '%%' + search.upper().replace(' ', '%%') + '%%'
    cursor = g.conn.execute(text("""WITH FullTable AS
          (SELECT P.purl, P.title, P.model, K.keyword, A.first_name,
          A.last_name, I.type, I.name, I.country, I.city
          FROM Papers P
          LEFT OUTER JOIN Is_Related_To IRT ON P.purl = IRT.purl
          LEFT OUTER JOIN Keywords K ON IRT.keyword = K.keyword
          LEFT OUTER JOIN Published_By PB ON P.purl = PB.purl
          LEFT OUTER JOIN Authors A ON PB.aid = A.aid
          LEFT OUTER JOIN Works_At WA ON WA.aid = A.aid
          LEFT OUTER JOIN Institutions I ON I.iid = WA.iid)
          SELECT DISTINCT FT.title, FT.purl
          FROM FullTable FT
          WHERE
          upper(FT.title) LIKE :string_match OR
          upper(FT.model) LIKE :string_match  OR
          upper(FT.keyword) LIKE :string_match OR
          upper(FT.first_name) LIKE :string_match OR
          upper(FT.last_name) LIKE :string_match OR
          upper(FT.name) LIKE :string_match OR
          upper(FT.type) LIKE :string_match OR
          upper(FT.country) LIKE :string_match OR
          upper(FT.city) LIKE :string_match;"""), string_match=string_match)
    results = []
    for r in cursor:
        results.append({'title': r.title, 'purl': utils.encode_url(r.purl)})
    return results


@app.route('/results/<search_word>')
def show_results(search_word):
    search_word = utils.decode_url(search_word)
    results = search_term(search_word)
    return render_template('results.html', results=results)


@app.route('/advanced', methods=['GET', 'POST'])
def advanced():
    search_form = AdvancedSearchForm()
    if search_form.validate_on_submit():
        if search_form.title:
            cursor = g.conn.execute(text("""
      WITH FullTable AS
      (SELECT P.purl, P.title, P.model, P.number_of_citations, R.programming_language, K.keyword, A.first_name,
      A.last_name, I.type, I.name, I.country, I.city, I.street, I.street_number, I.zip, R.rdate_published, P.date_published
      FROM Papers P
      LEFT OUTER JOIN Published_On PO ON P.purl = PO.purl
      LEFT OUTER JOIN Repositories R ON PO.url = R.url
      LEFT OUTER JOIN Is_Related_To IRT ON PO.purl = IRT.purl
      LEFT OUTER JOIN Keywords K ON IRT.keyword = K.keyword
      LEFT OUTER JOIN Published_By PB ON P.purl = PB.purl
      LEFT OUTER JOIN Authors A ON PB.aid = A.aid
      LEFT OUTER JOIN Works_At WA ON WA.aid = A.aid
      LEFT OUTER JOIN Institutions I ON I.iid = WA.iid)
      SELECT DISTINCT FT.title, FT.purl, FT.programming_language, FT.rdate_published
      FROM FullTable FT
      WHERE
      upper(FT.title) LIKE '%%' || :title || '%%' AND
      upper(FT.model) LIKE '%%' || :model || '%%' AND
      FT.date_published >= :pdate AND 
      FT.number_of_citations >= :citations AND
      upper(FT.first_name) LIKE '%%' || :first || '%%' AND
      upper(FT.last_name) LIKE '%%' || :last || '%%' AND
      upper(FT.name) LIKE '%%' || :institution || '%%' AND
      FT.type IN :insttype AND
      upper(FT.country) LIKE '%%' || :instcountry || '%%' AND
      upper(FT.city) LIKE '%%' || :instcity || '%%' AND
      upper(FT.zip) LIKE '%%' || :instzip || '%%' AND
      upper(FT.street) LIKE '%%' || :inststreet || '%%' AND
      upper(FT.street_number) LIKE '%%' || :instno || '%%';
      """), title=search_form.title.data.upper(), model=search_form.model.data.upper(),
            pdate=str(
                search_form.published_year.data if search_form.published_year.data else 1900) + '01' + '01',
            citations=search_form.minimum_citations.data if search_form.minimum_citations.data else 0,
            prog=search_form.repo_programming_language.data.upper(),
            rdate=str(
                search_form.repo_published_year.data if search_form.repo_published_year.data else 1900) + '01' + '01',
            first=search_form.author_first_name.data.upper(),
            last=search_form.author_last_name.data.upper(), institution=search_form.inst_name.data.upper(),
            insttype=tuple(search_form.inst_type.data.split(' ')),
            instcountry=search_form.inst_country.data.upper(), instcity=search_form.inst_city.data.upper(),
            instzip=search_form.inst_zip.data.upper(),
            inststreet=search_form.inst_street.data.upper(), instno=search_form.inst_street_no.data.upper())
        results = []
        for r in cursor:
            if (search_form.repo_programming_language.data != '' and
                    (not r.programming_language or
                    r.programming_language.upper() != search_form.repo_programming_language.data.upper())):
                continue
            if (search_form.repo_published_year.data is not None and
                    (not r.rdate_published or
                    r.rdate_published.year < search_form.repo_published_year.data)):
                continue
            results.append({'title': r.title, 'purl': utils.encode_url(r.purl)})
        return render_template('advancedsearch.html', results=results)
    return render_template('advanced.html', form=search_form)


# pprint(vars(search_form))


@app.route('/details/<purl>', methods=['GET', 'POST'])
def paper_details(purl):
    purl = utils.decode_url(purl)
    try:
        store_history(purl)
    except:
        pass
    cursor = g.conn.execute(text("""
        SELECT  P.title, P.purl, P.model, PO.url
        FROM Papers P LEFT OUTER JOIN Published_On PO ON P.purl = PO.purl
        WHERE P.purl = :purl;
      """), purl=purl)
    paper = cursor.fetchone()
    cursor = g.conn.execute(text("""
      SELECT  PB.aid, A.first_name, A.last_name, I.iid, I.name
      FROM Papers P RIGHT OUTER JOIN Published_by PB ON P.purl = PB.purl
      INNER JOIN Authors A ON PB.aid = A.aid
      INNER JOIN Works_At WA ON WA.aid = A.aid
      INNER JOIN Institutions I ON I.iid = WA.iid
      WHERE P.purl = :purl;
    """), purl=purl)
    authors = list(cursor.fetchall())
    cursor.close()
    return render_template('paper_details.html', paper=paper, authors=authors)


def store_history(purl):
    global USER
    if not USER:
        return
    today = datetime.datetime.now().date()
    get_cursor = g.conn.execute(text("""
  SELECT * FROM Have_Read HR
  WHERE HR.user_name = :user_name AND HR.purl = :purl AND HR.date = :date;
  """), user_name=USER['user_name'], purl=purl, date=today)
    result = get_cursor.fetchone()
    if result:
        return
    insert_cursor = g.conn.execute(text("""
  INSERT INTO Have_Read(user_name, purl, date)
  VALUES (:user_name, :purl, :date);
  """), user_name=USER['user_name'], purl=purl, date=today)
    insert_cursor.close()


@app.route('/my-account', methods=['GET', 'POST'])
def my_account():
    global USER
    if not USER:
        return redirect('/login')
    user_cursor = g.conn.execute(text("""
    SELECT *
    FROM Users U
    WHERE U.user_name = :username;
    """), username=USER['user_name'])
    user = user_cursor.fetchone()
    history_cursor = g.conn.execute(text("""
    SELECT P.purl, P.title, HR.date
    FROM Have_Read HR INNER JOIN Papers P ON P.purl = HR.purl
    WHERE HR.user_name = :username
    ORDER BY HR.date DESC
    """), username=USER['user_name'])
    recommendations = recommender()
    history = []
    for h in history_cursor:
        h = {'title': h.title, 'purl': utils.encode_url(h.purl), 'date': h.date}
        history.append(h)
    context = {'user': user, 'history': history, 'recommendations': recommendations}
    return render_template("my_account.html", **context)


@app.route('/institutions', methods=['GET', 'POST'])
def institutions():
    institutions_cursor = g.conn.execute("""
      SELECT *
      FROM Institutions I
    """)
    institutions_list = []
    for i in institutions_cursor:
        institutions_list.append(i)
    return render_template('institutions.html', institutions=institutions_list)


@app.route('/institution/<iid>', methods=['GET', 'POST'])
def institution_detail(iid):
    institution_cursor = g.conn.execute(text("""
    SELECT *
    FROM Institutions I
    WHERE I.iid = :iid
    """), iid=iid)
    details = institution_cursor.fetchone()
    authors_cursor = g.conn.execute(text("""
        SELECT A.aid, A.first_name, A.last_name
        FROM Authors A
        INNER JOIN Works_At WA ON WA.aid = A.aid
        INNER JOIN Institutions I ON I.iid = WA.iid
        WHERE I.iid = :iid
        ORDER BY A.last_name
        """), iid=iid)
    authors = authors_cursor.fetchall()
    p_cursor = g.conn.execute(text("""
        SELECT DISTINCT P.title, P.purl, P.number_of_citations
        FROM Papers P
        INNER JOIN Published_By PB ON PB.purl = P.purl
        INNER JOIN Authors A ON PB.aid = A.aid
        INNER JOIN Works_At WA ON WA.aid = A.aid
        INNER JOIN Institutions I ON I.iid = WA.iid
        WHERE I.iid = :iid
        ORDER BY P.number_of_citations DESC
        """), iid=iid)
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
    cursor = g.conn.execute(text("""
    SELECT A.first_name, A.last_name, I.name as inst_name, I.iid
    FROM Authors A INNER JOIN Works_At WA ON WA.aid = A.aid
    INNER JOIN Institutions I ON I.iid = WA.iid
    WHERE A.aid = :aid
    """), aid=aid)
    details = cursor.fetchone()
    cursor = g.conn.execute(text("""
    SELECT DISTINCT P.purl, P.title, P.number_of_citations
    FROM Authors A INNER JOIN Published_By PB ON A.aid = PB.aid
    INNER JOIN Papers P ON P.purl = PB.purl
    WHERE A.aid = :aid
    ORDER BY P.number_of_citations DESC
    """), aid=aid)
    papers = []
    for p in cursor:
        new_p = {'purl': utils.encode_url(p.purl), 'title': p.title, 'citations': p.number_of_citations}
        papers.append(new_p)
    context = {'author': details, 'papers': papers}
    return render_template('author_details.html', **context)


def recommender():
    global USER
    if not USER:
        return []
    s = text("""
    SELECT P1.title, P1.purl
    FROM Papers P1 NATURAL JOIN Is_Related_To I 
    WHERE P1.purl = I.purl AND I.keyword IN (SELECT IR.keyword FROM Is_Related_To IR WHERE IR.purl IN (SELECT P.purl
    FROM Papers P NATURAL JOIN Have_Read HR
    WHERE P.purl = HR.purl AND HR.user_name = :user_name))
    EXCEPT 
    SELECT SUB.title, SUB.purl
    FROM (SELECT * FROM Papers P2 NATURAL JOIN Have_Read HR2 
    WHERE P2.purl = HR2.purl AND HR2.user_name = :user_name
    ORDER BY HR2.date) AS SUB
    LIMIT 3;
    """)
    cursor = g.conn.execute(s, user_name=USER['user_name'])
    recommendations = []
    for r in cursor:
        recommendations.append({'title': r.title, 'purl': utils.encode_url(r.purl)})
    return recommendations


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
