from flask_extended import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from flask import request, send_from_directory, abort
from flask_cors import CORS
from datetime import datetime
import os
import json

app = Flask(__name__)

app.config.from_yaml(os.path.join(app.root_path, 'config/config.yaml'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging_file = f"logs-{datetime.now()}".replace(" ", "_")

CORS(app, resources={r'/*': {'origins': '*'}})

class Todos(db.Model):
    __tablename__ = "todos"
    
    id = db.Column(db.Integer, primary_key='true')
    text = db.Column(db.String())
    date = db.Column(db.Date())
    done = db.Column(db.Boolean())
    comment = db.Column(db.String())

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def __init__(self, text):
        self.text = text
        self.date = datetime.now()
        self.done = False
        self.comment = ""
    
    def serialize(self):
        return {
            'id': self.id,
            'text': self.text,
            'date': str(self.date).replace(" ", "_"),
            'done': self.done
        }

class SubTasks(db.Model):
    __tablename__ = "subtasks"

    id = db.Column(db.Integer, primary_key='true')
    super_task = db.Column(db.Integer, ForeignKey('todos.id'))
    text = db.Column(db.String())
    date = db.Column(db.Date())
    done = db.Column(db.Boolean())
    comment = db.Column(db.String())

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def __init__(self, text, parent_id):
        self.text = text
        self.super_task = parent_id
        self.date = datetime.now()
        self.done = False
        self.comment = ""

    def serialize(self):
        return {
            'id': self.id,
            'parent_id': self.super_task,
            'text': self.text,
            'date': str(self.date).replace(" ", "_"),
            'done': self.done
        }

db.create_all()

@app.route("/api/add", methods=['POST'])
def add_todo():
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text')
        todo = Todos(text)
        add_to_logs("Added todo: " + text)
        db.session.add(todo)
        db.session.commit()
        return "success"

@app.route("/api/addsubtask", methods=['POST'])
def add_sub_task():
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text')
        parent_id = data.get('id')
        todo = SubTasks(text, parent_id)
        add_to_logs(f"Added subtask of task {parent_id}: {text}")
        db.session.add(todo)
        db.session.commit()
        return "success"

@app.route("/api/list")
def get_todolist():
    list = Todos.query.all()
    rets = []
    for todo in list:
        todo = todo.serialize()
        subTasks = SubTasks.query.filter_by(super_task=todo.get('id')).all()
        todo['subtasks'] = json.dumps([x.serialize() for x in subTasks])
        rets.append(todo)
    return json.dumps(rets)

@app.route("/api/remove", methods=['POST'])
def remove_todo():
    if request.method == 'POST':
        data = request.get_json()
        origional_text = Todos.query.filter_by(id=data.get('id')).first().text
        SubTasks.query.filter_by(super_task=data.get('id')).delete()
        Todos.query.filter_by(id=data.get('id')).delete()
        add_to_logs(f"Removed todo id {request.get_json().get('id')}: \"{origional_text}\"")
        db.session.commit()
        return "success"

@app.route("/api/done", methods=['POST'])
def mark_done():
    if request.method == 'POST':
        data = request.get_json()
        origional_status = bool(Todos.query.filter_by(id=data.get('id')).first().done)
        Todos.query.filter_by(id=data.get('id')).update({"done": not origional_status })
        add_to_logs(f"Changed status todo id {request.get_json().get('id')}: \"{origional_status}\" to \"{not origional_status}\"")
        db.session.commit()
        return "success"

@app.route("/api/edit", methods=['POST'])
def edit_todo():
    if request.method == 'POST':
        data = request.get_json()
        origional_text = Todos.query.filter_by(id=data.get('id')).first().text
        Todos.query.filter_by(id=data.get('id')).update({"text": data.get('text')})
        add_to_logs(f"Changed todo id {request.get_json().get('id')}: \"{origional_text}\" to \"{data.get('text')}\"")
        db.session.commit()
        return "success"

@app.route("/api/export", methods=['GET'])
def get_export():
    if request.method == 'GET':
        filename = f'export-{datetime.now()}.csv'
        filename = filename.replace(" ", "_")
        with open(f'./exports/{filename}', 'w') as file:
            file.write(sql_query_to_csv(Todos.query.all(), ['_sa_instance_state']))
        try:
            return send_from_directory(directory="./exports/", path=filename, as_attachment=True)
        except FileNotFoundError:
            abort(404) 

@app.route("/api/logs", methods=['GET'])
def get_logs():
    if request.method == 'GET':
        try:
            return send_from_directory(directory="./logs/", path=logging_file, as_attachment=True)
        except FileNotFoundError:
            abort(404)

def sql_query_to_csv(query_output, columns_to_exclude=""):
    """ Converts output from a SQLAlchemy query to a .csv string.

    Parameters:
     query_output (list of <class 'SQLAlchemy.Model'>): output from an SQLAlchemy query.
     columns_to_exclude (list of str): names of columns to exclude from .csv output.

    Returns:
     csv (str): query_output represented in .csv format.

    Example usage:
     users = db.Users.query.filter_by(user_id=123)
     csv = sql_query_to_csv(users, ["id", "age", "address"]
    """
    rows = query_output
    columns_to_exclude = set(columns_to_exclude)

    #create list of column names  
    column_names = [i for i in rows[0].__dict__]
    for column_name in columns_to_exclude:
        column_names.pop(column_names.index(column_name))
    
    #add column titles to csv
    column_names.sort()
    csv = ", ".join(column_names) + "\n"
    
    #add rows of data to csv
    for row in rows:
        for column_name in column_names:
            if column_name not in columns_to_exclude:
                data = str(row.__dict__[column_name])
                #Escape (") symbol by preceeding with another (")
                data.replace('"','""')
                #Enclose each datum in double quotes so commas within are not treated as separators
            csv += '"' + data + '"' + ","
        csv += "\n"
    
    return csv

def add_to_logs(input):
    with open("./logs/" + logging_file, 'a') as file:
        file.write(str(datetime.now()) + " - " + input + "\n")


if __name__ == '__main__':
    add_to_logs("Server is starting")
    app.run()
