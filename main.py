from flask import Flask, render_template, request
from sqlalchemy import create_engine, text

app = Flask(__name__) 

conn_str = "mysql://root:cset155@localhost/examdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


@app.route('/')
def index():
    result = conn.execute(text("SELECT * FROM boats")).fetchall()
    boats = [dict(row._mapping) for row in result]
    return render_template('index.html', boats=boats)





if __name__ == '__main__':
    app.run(debug=True)