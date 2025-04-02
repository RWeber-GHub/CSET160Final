from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, text
import logging
import tkinter as tk
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
    statement = "select * from accounts"
    parameters = {}
    if request.method == 'POST':
        account_type = request.form.get('type', '')
        name = request.form.get('name')
        date = request.form.get('date')
        if account_type:
            statement += " where type = :type"
            parameters['type'] = account_type
        if name or date:
            statement += " order by"
            if name:
                if name == 'A':
                    statement += " username ASC"
                elif name == 'B':
                    statement += " username DESC"
            if date:
                if name:
                    statement += ","
                if date == 'A':
                    statement += " date_created ASC"
                elif date == 'B':
                    statement += " date_created DESC"
    accounts = conn.execute(text(statement), parameters).all()
    return render_template('accountdirectory.html', accounts=accounts)

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    if user_id:
        return f"User ID: {user_id}"+f"User Type: {user_type}"
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
                user_type = user[3]
                session['user_id'] = user_id
                session['user_type'] = user_type
            if  session.get('user_type') == 'A':
                return redirect(url_for("testviewer"))
            if session.get('user_type') == 'B':
                return redirect(url_for("testviewer"))
            else:
                return render_template('login.html', error="Incorrect Username or Password")
        except Exception as e:
            print(f"Error: {e}")
            return render_template('login.html', error="An error occurred during login.")
    return render_template('login.html')

@app.route('/signout', methods=['POST'])
def process():
    if request.method == 'POST':
        session.pop('user_type', None)
        session.pop('user_id', None)
        return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        account_type = request.form['type']
        try:
            conn.execute(text("insert into accounts (username, password, type) values (:username, :password, :type)"), {'username': username, 'password': password, 'type': account_type})
            conn.commit()
            result = conn.execute(text("select * from accounts where username = :username and password = :password"), {'username': username, 'password': password})
            user = result.fetchone()
            user_id = user[0]
            user_type = user[3]
            session['user_id'] = user_id
            session['user_type'] = user_type
            return redirect(url_for("testviewer"))
        except Exception as e:
            print(f"Error: {e}")
            return render_template('signup.html', error="Username is taken.")
    return render_template('signup.html')


@app.route('/testviewer', methods=['GET', 'POST'])
def testviewer():
    if 'user_type' not in session:
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))

    user_type = session['user_type']

    try:
        with engine.connect() as conn:
            if user_type == 'B':
                if request.method == 'POST':  
                    action = request.form.get('action')
                    
                    if action == 'edit':
                        test_id = request.form.get('testid')
                        return redirect(url_for('edit_test', test_id=test_id))
        
                    if action == 'grade':
                        testid = request.form.get('testid')
                        grade = request.form.get('grade')
                        results = conn.execute(text('select * from responses where testid = :testid'),  {'testid': testid}).all()
                        if results:
                            for result in results:
                                user_id = result[0]
                        if grade:
                            grade = f"{grade}/100"
                            conn.execute(text("insert into grades (id, testid, grade) VALUES (:id, :testid, :grade)"), {'id': user_id, 'testid': testid, 'grade': grade})
                            conn.commit()
                    else:
                        flash("Please provide a valid grade", "danger")
                    return redirect(url_for('testviewer'))
        

                user_id = session.get('user_id')  

                query = text("""
                    select r.testid, r.id as id, t.name as name, 
                    r.response_1, r.response_2, r.response_3, r.response_4, r.response_5, 
                    g.grade
                    from responses r
                    join tests t on r.testid = t.testid 
                    left join grades g on r.testid = g.testid and r.id = g.id
                    where t.id = :user_id
                    and g.grade is null and r.id != :user_id
                """)

                result = conn.execute(query, {'user_id': user_id}).fetchall()
                print(f'***{result}***')

                responses = [
                    {
                        'testid': row.testid,
                        'id': row.id,
                        'name': row.name,
                        'grade': row.grade,
                        'response_1': row.response_1,
                        'response_2': row.response_2,
                        'response_3': row.response_3,
                        'response_4': row.response_4,
                        'response_5': row.response_5
                    }
                    for row in result
                ]
                
                print(f'***{responses}***')

                test = text("select * from tests where id = :user_id")
                tests = conn.execute(test, {'user_id': user_id}).all()
                tests = [dict(row._mapping) for row in tests]

                return render_template('teacher_view.html', tests=tests, responses=responses)

            elif user_type == 'A':
                tests = conn.execute(text('SELECT * FROM tests')).fetchall()
                user_id = session['user_id']
                grades = conn.execute(text('select * from grades where id = :user_id'),  {'user_id': user_id}).fetchall()
                tests = [dict(row._mapping) for row in tests]
                grades = [dict(row._mapping) for row in grades]

                return render_template('student_view.html', tests=tests, grades=grades)

    except Exception as e:
        logging.error(f"Error: {e}")
        flash("An error occurred while loading the tests.", "danger")
        return redirect(url_for('index'))
    
@app.route('/grade_response', methods=['POST'])
def grade_response():
    testid = request.form.get('testid')
    id = request.form.get('id') 
    grade = request.form.get('grade')
    print(f'***{id,testid,grade}***')
    try:
        conn.execute(text("insert into grades (id, testid, grade) VALUES (:id, :testid, :grade)"), {'id': id, 'testid': testid, 'grade': grade})
        conn.commit()
        return redirect(url_for('testviewer'))
    except Exception as e:
        flash(f"Error occurred: {str(e)}", "error")
        return redirect(url_for('testviewer'))

@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
def edit_test(test_id):
    if session.get('user_type') != 'B':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))

    try:
        with engine.connect() as conn:
            if request.method == 'POST': 
                question_1 = request.form['question_1']
                question_2 = request.form['question_2']
                question_3 = request.form['question_3']
                question_4 = request.form['question_4']
                question_5 = request.form['question_5']
                name = request.form['name']

                if not (question_1 and question_2 and question_3 and question_4 and question_5 and name):
                    flash('Please fill out all fields.', 'warning')
                    return redirect(url_for('edit_test', test_id=test_id))

                conn.execute(
                    text('''
                        UPDATE tests
                        SET name = :name, question_1 = :q1, question_2 = :q2, question_3 = :q3, 
                            question_4 = :q4, question_5 = :q5
                        WHERE testid = :testid
                    '''),
                    {
                        'name': name,
                        'q1': question_1,
                        'q2': question_2,
                        'q3': question_3,
                        'q4': question_4,
                        'q5': question_5,
                        'testid': test_id
                    }
                )
                conn.commit() 
                flash("Test updated successfully!", "success")
                return redirect(url_for('testviewer'))  

            result = conn.execute(text('SELECT * FROM tests WHERE testid = :test_id'), {'test_id': test_id}).fetchone()

            if not result:
                flash('Test not found.', 'danger')
                return redirect(url_for('testviewer'))

            test = dict(result._mapping)

            return render_template('edit_test.html', test=test)  

    except Exception as e:
        logging.error(f"Error: {e}")
        flash("An error occurred while updating the test.", "danger")
        return redirect(url_for('testviewer'))

@app.route('/create_test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
        try:
            username = request.form.get('username')  
            name = request.form.get('name')
            question_1 = request.form.get('question_1')
            question_2 = request.form.get('question_2')
            question_3 = request.form.get('question_3')
            question_4 = request.form.get('question_4')
            question_5 = request.form.get('question_5')
            if not (username and name and question_1 and question_2 and question_3 and question_4 and question_5):
                flash('Please fill out all fields.', 'warning')
                return redirect(url_for('create_test'))
            id_result = conn.execute(text('SELECT id FROM accounts WHERE username = :username'), {'username': username}).fetchone()
            id = id_result[0] if id_result else None
            result = conn.execute(text("SHOW TABLE STATUS LIKE 'tests'"))
            row = result.mappings().fetchone()
            testid = row['Auto_increment'] if row else None
            conn.execute(
                text('''
                    INSERT INTO tests (testid, id, name, question_1, question_2, question_3, question_4, question_5)
                    VALUES (:testid, :id, :name, :q1, :q2, :q3, :q4, :q5)
                '''),
                {
                    'testid': testid, 
                    'id': id,
                    'name': name,
                    'q1': question_1,
                    'q2': question_2,
                    'q3': question_3,
                    'q4': question_4,
                    'q5': question_5
                }
            )
            
            conn.commit()
            flash('Test created successfully!', 'success')
            return redirect(url_for('testviewer'))

        except Exception as e:
            flash(f'Error creating test: {str(e)}', 'danger')
            return redirect(url_for('create_test'))

    return render_template('test_maker.html')


@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    try:
        conn.execute(
            text('DELETE FROM responses WHERE testid = :test_id'),
            {'test_id': test_id}
        )
        result = conn.execute(
            text('DELETE FROM tests WHERE testid = :test_id'),
            {'test_id': test_id}
        )
        conn.commit()

        if result.rowcount > 0:
            flash('Test deleted successfully.', 'success')
        else:
            flash('Test not found or already deleted.', 'warning')

    except Exception as e:
        flash(f'Error deleting test: {str(e)}', 'danger')

    return redirect(url_for('testviewer'))

@app.route('/test/<int:testid>')
def view_test(testid):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view the test.", "danger")
        return redirect(url_for('login'))

    with engine.connect() as conn:
        stmt = text('''
            SELECT COUNT(*) FROM responses
            WHERE testid = :testid AND id = :user_id
        ''')
        result = conn.execute(stmt, {'testid': testid, 'user_id': user_id}).scalar()
        has_taken_test = result > 0

    return render_template('test.html', testid=testid, has_taken_test=has_taken_test)

@app.route('/submit_test/<int:testid>', methods=['POST'])
def submit_test(testid):
    
    if session.get('user_type') != 'A':
        flash("You do not have permission to submit responses.", "danger")
        return redirect(url_for('testviewer'))

  
    user_id = session.get('user_id')
    if not user_id:
        flash("User ID not found. Please log in again.", "danger")
        return redirect(url_for('login'))

    
    try:
        with engine.connect() as conn:
            stmt = text('''
                SELECT COUNT(*) FROM responses
                WHERE testid = :testid AND id = :user_id
            ''')
            result = conn.execute(stmt, {'testid': testid, 'user_id': user_id}).scalar()

           
            if result > 0:
                flash("You have already taken this test.", "warning")
                return redirect(url_for('testviewer'))
            

    except Exception as e:
        print('error')
        flash(f"Error checking test status: {str(e)}", "danger")
        return redirect(url_for('testviewer'))

    
    required_fields = ['response_1', 'response_2', 'response_3', 'response_4', 'response_5']
    if not all(field in request.form for field in required_fields):
        flash("Missing form data!", "danger")
        return redirect(url_for('testviewer'))

   
    responses = {
        'response_1': request.form['response_1'],
        'response_2': request.form['response_2'],
        'response_3': request.form['response_3'],
        'response_4': request.form['response_4'],
        'response_5': request.form['response_5']
    }
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            stmt = text('''
                INSERT INTO responses (id, testid, response_1, response_2, response_3, response_4, response_5)
                VALUES (:user_id, :testid, :r1, :r2, :r3, :r4, :r5)
            ''')

            conn.execute(stmt, {
                'user_id': user_id,
                'testid': testid, 
                'r1': responses['response_1'],
                'r2': responses['response_2'],
                'r3': responses['response_3'],
                'r4': responses['response_4'],
                'r5': responses['response_5']
            })
            print(user_id, testid, responses['response_1'],responses['response_2'],responses['response_3'],responses['response_4'],responses['response_5'])
            trans.commit()
            flash('Responses submitted successfully!', 'success')

    except Exception as e:
        flash(f"Error submitting responses: {str(e)}", "danger")

    return redirect(url_for('testviewer'))


if __name__ == '__main__':
    app.run(debug=True)