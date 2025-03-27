from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__) 

conn_str = "mysql://root:cset155@localhost/examdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/')
def index():
    tests = conn.execute(text('select * from tests')).all()
    return render_template('index.html', tests = tests)

@app.route('/account_directory')
def accountDirectory():
    accounts = conn.execute(text('select * from accounts')).all()
    return render_template('accountdirectory.html', accounts = accounts)

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/login',  methods=['GET', 'POST'])
def login():
    accounts = conn.execute(text('select * from accounts')).all()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn.execute(text("select * from accounts where username = :username and password = :password"), {'username': username, 'password': password})
            return redirect(url_for("index"))
        except Exception as e:
            print(f"Error: {e}")
    return render_template('login.html', accounts=accounts)

@app.route('/signup',  methods=['GET', 'POST'])
def signup():
    accounts = conn.execute(text('select * from accounts')).all()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        account_type = request.form['type']
        if account_type == 'student':
            account_type = 'A'
        else:
            account_type = 'B'
        try:
            conn.execute(text("insert into accounts (username, password, type) values (:username, :password, :type)"), {'username': username, 'password': password, 'type': account_type})
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
    return render_template('signup.html', accounts=accounts)

@app.route('/testview', methods=['GET', 'POST'])
def testviewer():
    tests = conn.execute(text('SELECT * FROM tests')).all()
    tests = [dict(row._mapping) for row in tests]
    if request.method == 'POST':
        print(tests)
    return render_template('testview.html', tests=tests)

@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
def edit_test(test_id):
    if request.method == 'POST':
        question_1 = request.form['question_1']
        question_2 = request.form['question_2']
        question_3 = request.form['question_3']
        question_4 = request.form['question_4']
        question_5 = request.form['question_5']

        conn.execute(
            text('''
                UPDATE tests 
                SET question_1 = :q1, question_2 = :q2, question_3 = :q3, question_4 = :q4, question_5 = :q5
                WHERE testid = :test_id
            '''),
            {'q1': question_1, 'q2': question_2, 'q3': question_3, 'q4': question_4, 'q5': question_5, 'test_id': test_id}
        )
        conn.commit()
        return redirect(url_for('testviewer'))

    result = conn.execute(text('SELECT * FROM tests WHERE testid = :test_id'), {'test_id': test_id}).fetchone()

    if result:
        test = dict(result._mapping)
        return render_template('edit_test.html', test=test)
    else:
        return "Test not found", 404

@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):

    conn.execute(text('DELETE FROM tests WHERE testid = :test_id'), {'test_id': test_id})
    conn.commit()
    return redirect(url_for('testviewer'))

if __name__ == '__main__':
    app.run(debug=True)