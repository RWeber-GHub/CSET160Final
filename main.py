from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, text
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__) 
app.secret_key = 'your_secret_key'


conn_str = "mysql://root:cset155@localhost/examdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/account_directory', methods=['GET', 'POST'])
def accountDirectory():
    if request.method == 'POST':
        account_type = request.form['type']
        accounts = conn.execute(text("select * from accounts where type = :type"), {'type': account_type}).all()
    else:
        accounts = conn.execute(text('select * from accounts')).all()
    return render_template('accountdirectory.html', accounts = accounts)

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if user_id:
        return f"User ID: {user_id}"
    else:
        return redirect(url_for('login')) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            result = conn.execute(text("select * from accounts where username = :username and password = :password"), {'username': username, 'password': password})
            user = result.fetchone()
            if user:
                user_id = user[0]
                session['user_id'] = user_id
                print(session.get('user_id'))
                return redirect(url_for("testviewer"))
            else:
                return render_template('login.html', error="Incorrect Username or Password")
        except Exception as e:
            print(f"Error: {e}")
            return render_template('login.html', error="An error occurred during login.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        account_type = request.form['type']
        print(username, password, account_type)
        try:
            conn.execute(text("insert into accounts (username, password, type) values (:username, :password, :type)"), {'username': username, 'password': password, 'type': account_type})
            conn.commit()
            result = conn.execute(text("select * from accounts where username = :username and password = :password"), {'username': username, 'password': password})
            user = result.fetchone()
            user_id = user[0]
            session['user_id'] = user_id
            print(session.get('user_id'))
            return redirect(url_for("testviewer"))
        except Exception as e:
            print(f"Error: {e}")
            return render_template('signup.html', error="Username is taken.")
    return render_template('signup.html')

@app.route('/testviewer', methods=['GET', 'POST'])
def testviewer():
    if request.method == 'POST':
        testid = request.form['testid']
        question_1 = request.form['question_1']
        question_2 = request.form['question_2']
        question_3 = request.form['question_3']
        question_4 = request.form['question_4']
        question_5 = request.form['question_5']

        conn.execute(
            text('''
                UPDATE tests
                SET question_1 = :q1, question_2 = :q2, question_3 = :q3, question_4 = :q4, question_5 = :q5
                WHERE testid = :testid
            '''),
            {
                'q1': question_1,
                'q2': question_2,
                'q3': question_3,
                'q4': question_4,
                'q5': question_5,
                'testid': testid
            }
        )
        conn.commit()
        flash('Test updated successfully!', 'success')
        return redirect(url_for('testviewer'))

    result = conn.execute(text('SELECT * FROM tests')).fetchall()
    tests = [dict(row._mapping) for row in result] 
    return render_template('testviewer.html', tests=tests)



@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    try:
        result = conn.execute(text('DELETE FROM tests WHERE testid = :test_id'), {'test_id': test_id})
        
        if result.rowcount == 0:
            flash('Test not found or already deleted.', 'warning')
        else:
            flash('Test deleted successfully.', 'success')

        conn.commit()
    except Exception as e:
        flash(f'Error deleting test: {str(e)}', 'danger')

    return redirect(url_for('testviewer'))


@app.route('/create_test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
        result = conn.execute(text("SHOW TABLE STATUS LIKE 'tests'"))
        row = result.mappings().fetchone()
        testid = row['Auto_increment'] if row else None

        username = request.form['username']
        id_result = conn.execute(text('SELECT id FROM accounts WHERE username = :username'), {'username': username}).fetchone()
        id = id_result[0] if id_result else None

        name = request.form['name']  
        question_1 = request.form['question_1']
        question_2 = request.form['question_2']
        question_3 = request.form['question_3']
        question_4 = request.form['question_4']
        question_5 = request.form['question_5']

        conn.execute(
            text('''
                INSERT INTO tests (testid, id, question_1, question_2, question_3, question_4, question_5, name)
                VALUES (:testid, :id, :q1, :q2, :q3, :q4, :q5, :name)
            '''),
            {'testid': testid, 'id': id, 'name': name, 'q1': question_1, 'q2': question_2, 'q3': question_3, 'q4': question_4, 'q5': question_5}
        )
        conn.commit()
        return redirect(url_for('testviewer'))

    return render_template('test_maker.html')




if __name__ == '__main__':
    app.run(debug=True)