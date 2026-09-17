from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = ("postgresql://postgres:postgres@localhost:5432/aurovia")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True, nullable = False)
    hashed_password = db.Column(db.String(500), nullable =False)
    role = db.Column(db.String(1), nullable = False)
    productIds= db.relationship('Products', backref = 'products', lazy = True )

class Products(db.Model):
    __tablename__ = 'products'
    productId = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable =False)
    haritIndex = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable= False)

with app.app_context():
    db.create_all()

@app.post('/register')
def register():
    body = request.get_json()
    username = body.get('username')
    password =body.get('password')
    role = body.get('role','C')
    if not username or not password:
        return jsonify({
            "error" : "Invalid request"
        }),400
    existing_user = Users.query.filter_by(username = username).first()
    if existing_user :
        return jsonify(
            {'error' : 'User With this username already exists'}
        ),409
    passwordHash = generate_password_hash(password)
    newUser = Users(username = username, hashed_password = passwordHash, role = role)
    db.session.add(newUser)
    db.session.commit()
    return jsonify({
        'Message': 'User successfully added'
    }),201

@app.get('/login')
def login():
    body = request.get_json()
    username = body.get('username')
    password = body.get('password')
    if not username or not password:
        return jsonify({
            "error" : "Invalid Request"
        }),400
    user  = Users.query.filter_by(username = username).first()
    if not user or not check_password_hash(user.hashed_password, password):
         return jsonify({
                    "error" : "Invalid Credentials"
                }),400
    return jsonify({
        "message" : "login successful"
    }),200

@app.post('/add-product')
def addProducts():
    body = request.get_json()
    user_id = body.get('user_id')
    productName = body.get('productName')
    materialType = body.get('materialType')
    manufacturingEmissions = body.get('manufacturingEmissions')
    recyclabilityScore = body.get('recyclabilityScore')
    logisticEmissions = body.get('logisticEmissions')
    certificationScore = body.get('certificationScore')
    user = Users.query.filter_by(user_id = user_id).first()
    if not user or user.role == 'C':
        return jsonify({
            'message' : 'Unauthorized Access'
        }), 401
    haritIndex = 0.2*materialType + 0.3 * manufacturingEmissions + 0.2 * recyclabilityScore + 0.2 * logisticEmissions + 0.1 * certificationScore
    newProduct = Products(name = productName, haritIndex = haritIndex, seller_id = user_id)
    db.session.add(newProduct)
    db.session.commit()
    return jsonify({
        "message" : "Product Successfully added"
    }),200

@app.get('/all-products')
def getAllProducts():
    products=  Products.query.order_by(Products.haritIndex.desc()).all()
    return jsonify([{
        "seller" : Users.query.filter_by(user_id = product.seller_id).first().username,
        "product" : product.name,
        "haritIndex" : product.haritIndex
       
    }for product in products]),200 

@app.get('/my-products/<int:user_id>')
def getMyProducts(user_id):
    products= Products.query.filter_by(seller_id = user_id).order_by(Products.haritIndex.desc()).all()
    return jsonify(
        [
            { 
                "seller" : Users.query.filter_by(user_id = product.seller_id).first().username,
                "product" : product.name,
                "haritIndex" : product.haritIndex
            } for product in products
        ]
    ),200

if __name__ == '__main__':
    app.run(debug=True)

    
