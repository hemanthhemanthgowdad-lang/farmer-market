from flask import Flask, render_template, request, redirect
import mysql.connector
import os

import pandas as pd
from sklearn.linear_model import LinearRegression

import requests

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Hemanth@1976",
    database="farmer_market"
)

print("Connected Successfully!")

# Home Page
@app.route('/')
def home():
    return redirect('/login')


# Add Crop
@app.route('/add', methods=['GET', 'POST'])
def add_crop():

    if request.method == 'POST':

        crop_name = request.form['crop_name']

        quantity = request.form['quantity']

        price = request.form['price']

        farmer_name = request.form['farmer_name']

        print("Farmer Name:", farmer_name)

        image = request.files['image']

        if image.filename == "":
            return "Please Select Image"

        filename = image.filename.replace(" ", "_")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        image.save(filepath)

        cursor = db.cursor()

        sql = """
        INSERT INTO crops
        (crop_name, quantity, price, image, farmer_name)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            crop_name,
            quantity,
            price,
            filename,
            farmer_name
        )

        print(values)

        cursor.execute(sql, values)

        db.commit()

        return redirect('/view')

    return render_template('add_crop.html')

# View + Search
@app.route('/view')
def view_crops():

    search = request.args.get('search')

    cursor = db.cursor()

    if search:

        sql = "SELECT * FROM crops WHERE crop_name LIKE %s"

        values = ("%" + search + "%",)

        cursor.execute(sql, values)

    else:

        cursor.execute("SELECT * FROM crops")

    crops = cursor.fetchall()

    total_crops = len(crops)

    total_quantity = 0

    total_price = 0

    for crop in crops:

        try:
            total_quantity += int(crop[2])

        except:
            pass

        try:
            total_price += int(crop[3])

        except:
            pass

    role = request.args.get('role')

    return render_template(
        'view.html',
        crops=crops,
        total_crops=total_crops,
        total_quantity=total_quantity,
        total_price=total_price,
        role=role
    )

# Delete
@app.route('/delete/<int:id>')
def delete_crop(id):

    cursor = db.cursor()

    sql = "DELETE FROM crops WHERE id=%s"

    values = (id,)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/view')


# Update
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_crop(id):

    cursor = db.cursor()

    if request.method == 'POST':

        crop_name = request.form['crop_name']
        quantity = request.form['quantity']
        price = request.form['price']

        sql = "UPDATE crops SET crop_name=%s, quantity=%s, price=%s WHERE id=%s"

        values = (crop_name, quantity, price, id)

        cursor.execute(sql, values)

        db.commit()

        return redirect('/view')

    sql = "SELECT * FROM crops WHERE id=%s"

    values = (id,)

    cursor.execute(sql, values)

    crop = cursor.fetchone()

    return render_template('update.html', crop=crop)


# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        cursor = db.cursor()

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"

        values = (email, password)

        cursor.execute(sql, values)

        user = cursor.fetchone()

        if user:

            role = user[4]

            if role == 'farmer':

                return redirect('/dashboard')

            else:

                return redirect('/customer')

        else:

            return "Invalid Email or Password"

    return render_template('login.html')


# Orders
@app.route('/orders')
def orders():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM orders")

    data = cursor.fetchall()

    return render_template('orders.html', orders=data)


# Register Farmer
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        sql = "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)"

        values = (name, email, password, 'farmer')

        cursor.execute(sql, values)

        db.commit()

        return "Registration Successful"

    return render_template('register.html')


# Farmer Login
@app.route('/farmer_login', methods=['GET', 'POST'])
def farmer_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        sql = "SELECT * FROM farmers WHERE email=%s AND password=%s"

        values = (email, password)

        cursor.execute(sql, values)

        farmer = cursor.fetchone()

        if farmer:

            return redirect('/view')

        else:

            return "Invalid Email or Password"

    return render_template('farmer_login.html')


# Order Crop
# Order Crop
@app.route('/order/<int:id>', methods=['GET', 'POST'])
def order_crop(id):

    cursor = db.cursor()

    sql = "SELECT * FROM crops WHERE id=%s"

    values = (id,)

    cursor.execute(sql, values)

    crop = cursor.fetchone()

    if request.method == 'POST':

        customer_name = request.form['customer_name']

        phone = request.form['phone']

        address = request.form['address']   

        quantity = request.form['quantity']

        unit = request.form['unit']

        full_quantity = quantity + " " + unit

        payment_method = request.form['payment_method']

        # Save Order
        sql2 = "INSERT INTO orders (crop_name, customer_name, phone, address, quantity, payment_method) VALUES (%s, %s, %s, %s, %s, %s)"

        values2 = (
            crop[1],
            customer_name,
            phone,
            address,
            full_quantity,
            payment_method
        )

        cursor.execute(sql2, values2)

        # Remove kg / ton from old quantity
        old_quantity = str(crop[2])

        old_quantity = old_quantity.replace("kg", "")

        old_quantity = old_quantity.replace("ton", "")

        old_quantity = old_quantity.strip()

        # Calculate new quantity
        new_quantity = int(old_quantity) - int(quantity)

        # Auto delete crop if quantity becomes 0
        if new_quantity <= 0:

            sql_delete = "DELETE FROM crops WHERE id=%s"

            cursor.execute(sql_delete, (id,))

            db.commit()

            return render_template('success.html')

        # Update quantity
        sql3 = "UPDATE crops SET quantity=%s WHERE id=%s"

        values3 = (str(new_quantity) + " " + unit, id)

        cursor.execute(sql3, values3)

        db.commit()

        return render_template('success.html')

    return render_template('order_form.html', crop=crop)
    

# Accept Order
@app.route('/accept/<int:id>')
def accept_order(id):

    cursor = db.cursor()

    sql = "UPDATE orders SET status='Accepted' WHERE id=%s"

    values = (id,)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/orders')


# Track Orders
@app.route('/track', methods=['GET', 'POST'])
def track():

    orders = []

    if request.method == 'POST':

        phone = request.form['phone']

        cursor = db.cursor()

        sql = "SELECT * FROM orders WHERE phone=%s"

        values = (phone,)

        cursor.execute(sql, values)

        orders = cursor.fetchall()

    return render_template('track.html', orders=orders)

@app.route('/dashboard')
def dashboard():

    api_key = "07549f8973bdc32c18d0b6fc4b9c4935"

    city = "Mysore"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    data = requests.get(url).json()

    if 'main' in data:

        temperature = data['main']['temp']

        weather = data['weather'][0]['main']

    else:

        temperature = "0"

        weather = "API Error"

    return render_template(
        'dashboard.html',
        temperature=temperature,
        weather=weather,
        city=city
    )
    

@app.route('/customer')
def customer():

    return render_template('customer.html')

@app.route('/logout')
def logout():

    return redirect('/login')


    return render_template('index.html')

@app.route('/weather')
def weather():

    lat = request.args.get('lat')

    lon = request.args.get('lon')

    api_key = "07549f8973bdc32c18d0b6fc4b9c4935"

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    data = requests.get(url).json()

    result = {
        "temp": data['main']['temp'],
        "weather": data['weather'][0]['main']
    }

    return result

@app.route('/prediction')
def prediction():

    days = [[1],[2],[3],[4],[5]]

    prices = [100,120,140,160,180]

    model = LinearRegression()

    model.fit(days, prices)

    future_day = [[6]]

    predicted_price = model.predict(future_day)

    price = round(predicted_price[0], 2)

    return render_template(
        'prediction.html',
        price=price
    )


# AI Crop Price Prediction

@app.route('/ai-price')
def ai_price():

    crops = {

        "Tomato": 4200,

        "Onion": 3800,

        "Rice": 2500,

        "Potato": 1900,

        "Mango": 5500,

        "Wheat": 3000

    }

    highest_crop = max(crops, key=crops.get)

    highest_price = crops[highest_crop]

    return render_template(
        'ai_price.html',
        crop=highest_crop,
        price=highest_price
    )

@app.route('/analytics')
def analytics():

    cursor = db.cursor()

    # Total Crops
    cursor.execute("SELECT COUNT(*) FROM crops")
    total_crops = cursor.fetchone()[0]

    # Total Orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # Total Farmers
    cursor.execute("SELECT COUNT(*) FROM users")
    total_farmers = cursor.fetchone()[0]

    # Total Revenue
    cursor.execute("SELECT SUM(price) FROM crops")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    return render_template(
        'analytics.html',
        total_crops=total_crops,
        total_orders=total_orders,
        total_farmers=total_farmers,
        revenue=revenue
    )

@app.route('/chatbot')
def chatbot():

    return render_template('chatbot.html')

@app.route('/chat')
def chat():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM chats ORDER BY id ASC")

    chats = cursor.fetchall()

    return render_template(
        'chat.html',
        chats=chats
    )

@app.route('/send_message', methods=['POST'])
def send_message():

    sender = request.form['sender']

    receiver = request.form['receiver']

    message = request.form['message']

    cursor = db.cursor()

    sql = "INSERT INTO chats(sender, receiver, message) VALUES(%s,%s,%s)"

    values = (sender, receiver, message)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/chat')
# Run Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)