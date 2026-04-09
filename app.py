from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth
from pymongo import MongoClient
import datetime

app = Flask(__name__)
CORS(app) # This allows your HTML pages to talk to this Python server

# --- 1. CONNECT TO FIREBASE ---
# Make sure you have downloaded the 'firebase-key.json' from Firebase Console
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# --- 2. CONNECT TO MONGODB ---
# Replace the string below with your ACTUAL connection string from MongoDB Atlas
MONGO_URI = "mongodb+srv://marcel_admin:<password>@cluster0.xxxx.mongodb.net/JambaWear?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["JambaWear"]

# --- 3. ROUTE: CHECK USER ROLE ---
@app.route('/api/check-role', methods=['POST'])
def check_role():
    data = request.json
    id_token = data.get('token')
    try:
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token['email']
        user_record = db.users.find_one({"email": email})
        
        if user_record:
            return jsonify({"role": user_record.get("role", "customer")})
        return jsonify({"role": "customer"})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

# --- 4. ROUTE: ADD PRODUCT (SELLER) ---
@app.route('/api/add-product', methods=['POST'])
def add_product():
    data = request.json
    try:
        # Calculate discount for the UI
        orig = float(data['original_price'])
        sell = float(data['selling_price'])
        data['discount_pct'] = round(((orig - sell) / orig) * 100)
        data['created_at'] = datetime.datetime.now()
        data['status'] = "pending" # Always starts as pending for Admin review

        result = db.products.insert_one(data)
        return jsonify({"status": "success", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- 5. ROUTE: GET PRODUCTS (FOR THE SHOP) ---
@app.route('/api/products', methods=['GET'])
def get_live_products():
    # Only send products that the admin has approved (status: live)
    products = list(db.products.find({"status": "live"}))
    for p in products:
        p['_id'] = str(p['_id'])
    return jsonify(products)

if __name__ == '__main__':
    # Run the server on your computer
    app.run(debug=True, port=5000)