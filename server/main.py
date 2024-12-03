from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'WarHead333'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///CodeCrib.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False 
app.config['SESSION_COOKIE_SECURE'] = False
db = SQLAlchemy(app)
CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    CheatSheets = db.relationship('CheatSheets', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class CheatSheets(db.Model):
    __tablename__ = "CheatSheets"
    id = db.Column(db.Integer, primary_key=True)
    sheetTitle = db.Column(db.String(20), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    CodeSheet = db.relationship('CodeSheets', backref='CheatSheets', lazy=True)

    def __repr__(self):
        return f'<sheetTitle {self.sheetTitle}>'

class CodeSheets(db.Model):
    __tablename__ = "CodeSheets"
    id = db.Column(db.Integer, primary_key=True)
    codeDesc = db.Column(db.String(200), nullable=False)
    codeSnippet = db.Column(db.String(1000), nullable=False)
    sheet_id = db.Column(db.Integer, db.ForeignKey('CheatSheets.id'), nullable=False)


    def __repr__(self):
        return f'<sheetID {self.id}>'
    

@app.route('/userSignup', methods=['GET', 'POST'])
def signup():

    data = request.json
    try:
        prevUser = User.query.filter_by(username=data['username'])
        if prevUser:
            return jsonify("Username Already Exists Try something new")

        new_user = User(username=data['username'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()

        response = "Registration Done Successfully"
        return jsonify(response)
    except Exception as e:
        return jsonify(e)

@app.route('/userLogin', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        data = request.get_json()
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.password == data['password']:
            session['uid'] = existing_user.id
            print("Login Successfully")
            return jsonify({'redirect_to': '/', 'username': data['username']})
    else:
        return jsonify("Welcome to CodeCrib")


@app.route('/createSheet', methods=['POST'])
def createSheet():
    data = request.get_json()
    try:
        if not data:
            return jsonify(error="Missing 'sheetTitle' in request"), 400

        user = User.query.filter_by(username=data['username']).first()
        uid = user.id
        existing_sheet = CheatSheets.query.filter_by(sheetTitle=data['sheetName'], user_id=uid).first()
        if existing_sheet:
            mess = data['sheetName']
            return jsonify(f"Sheet title '{mess}' already exists!")
        
        new_sheet = CheatSheets(
            sheetTitle=data['sheetName'],
            user_id=uid,
        )
        db.session.add(new_sheet)
        db.session.commit()

        return jsonify("CheatSheet added successfully")

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@app.route("/showSheets", methods=["POST"])
def showSheets():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")

    if request.method == 'POST':
        try:
            uname = request.get_json()

            user = User.query.filter_by(username=uname).first()
            if user:
                uid = user.id

            Sheets = CheatSheets.query.filter_by(user_id=uid).all()
            sheets_data = [{"id": sheet.id, "title": sheet.sheetTitle} for sheet in Sheets]

            # Debug print for sheet titles
            for sheet in Sheets:
                print(f"Sheet Title: {sheet.sheetTitle}")

            return jsonify({"sheets": sheets_data}), 201

        except Exception as e:
            return jsonify(f'{e}'), 500


@app.route('/deleteSheet', methods=['POST'])
def deleteSheet():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")
    
    if request.method == 'POST':
        try:
            sheetID = request.get_json()
            
            sheet = CheatSheets.query.get(sheetID)
            codes = CodeSheets.query.filter_by(sheet_id=sheetID).all()
            
            for code in codes:
                db.session.delete(code)
            
            db.session.delete(sheet)
            db.session.commit()
            return jsonify("Sheet Deleted Successfully")
        
        except Exception as e:
            return jsonify(f'{e}'), 500
    

@app.route('/addCode', methods=['POST'])
def addCode():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")

    if request.method == 'POST':
        try:
            data = request.get_json()
            code = data['code']
            codeDesc = data['codeDesc']
            codeTitle = data['codeTitle']
            
            if not code or not codeTitle:
                return jsonify("Please enter the Code")

            sheet = CheatSheets.query.filter_by(sheetTitle=codeTitle).first()
            new_code = CodeSheets(codeSnippet=code, codeDesc=codeDesc, sheet_id=sheet.id)
            db.session.add(new_code)
            db.session.commit()
            
            return jsonify("Code Added Successfully")
        
        except Exception as e:
            return jsonify(f'{e}'), 500
    

@app.route('/showCode', methods=['POST'])
def showCode():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            sheet = CheatSheets.query.filter_by(sheetTitle=data).first()
            
            if sheet:
                sheetID = sheet.id
            
            codes = CodeSheets.query.filter_by(sheet_id=sheetID).all()
            code_data = [{"id": code.id, "codeDesc": code.codeDesc, "code": code.codeSnippet} for code in codes]

            for code in codes:
                print(f"code Title: {code.codeDesc}")
                print(f"code Title: {code.codeSnippet}")

            return jsonify({"code_data": code_data}), 201

        except Exception as e:
            return jsonify(f'{e}'), 500
    
@app.route("/delCode", methods=["POST"])
def delCode():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")

    if request.method == 'POST':
        try:
            data = request.get_json()
            
            code = CodeSheets.query.get(data)
            db.session.delete(code)
            db.session.commit()
            return jsonify("Snippet Deleted Successfully")
            
        except Exception as e:
            return jsonify(f'{e}'), 500
    
@app.route("/editCode", methods=["POST"])
def editCode():
    if request.content_type != 'application/json':
        return jsonify("Welcome to CodeCrib Server")

    if request.method == 'POST':
        try:
            data = request.get_json()
            print(data)
            codeTable = CodeSheets.query.get(data['id'])
            codeTable.codeSnippet = data['code']
            db.session.commit()
            return jsonify("Code Edited Successfully")
        except Exception as e:
            return jsonify(f'{e}'), 500


if '__main__' == __name__:
    with app.app_context():
        db.create_all()
    app.run(debug=True)