import io
from flask import Flask, render_template,request,jsonify
from flask_cors import CORS
from datetime import date
from flask_mysqldb import MySQL
import qrcode
import random
from PIL import Image
import base64

app = Flask(__name__)

app.config['MYSQL_HOST']= 'db4free.net'
app.config['MYSQL_USER']= 'rooter2'
app.config['MYSQL_PASSWORD']= '12345678'
app.config['MYSQL_DB']= 'project_kart'

mysql= MySQL(app)

today = date.today()

app.config.from_object(__name__)
CORS(app, resources={r"/*":{'origins':"*"}})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_card', methods=['POST'])
def create_card():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        cur = mysql.connection.cursor()
        
        sql="SELECT MAX(id) + 1 AS next_id FROM users"
        cur.execute(sql)
        result = cur.fetchone()
        next_id = result[0]

        if next_id is None:
            next_id=1    
        
        def check_if_exists(num):
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE secret = %s", (num,))
            res = cur.fetchone()
            if res:
                secret = random.randint(10000000, 99999999)
                return check_if_exists(secret)
            else:
                return num

        secret = random.randint(10000000, 99999999)
        key = check_if_exists(secret)
        
        print(key)
        # cur.execute("SELECT email FROM users WHERE secret = %s", (key,))
        # check_if_email_exists = cur.fetchone()
        # if check_if_email_exists is not None:
        #     print('Email already exists')

        
        query = "INSERT INTO users (id,secret,name,email,phone,created_date,deleted) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cur.execute(query, (next_id,key,name,email,phone,today,0))
        
        mysql.connection.commit()
        cur.close()
    
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        url = 'http://127.0.0.1:5000/getUser/' + str(key)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert the QR code image to a byte stream
        img_byte_stream = io.BytesIO()
        qr_img.save(img_byte_stream, format='PNG')
        img_byte_stream.seek(0)

        # Encode the byte stream as base64
        qr_code_base64 = base64.b64encode(img_byte_stream.read()).decode('utf-8')

        # Render the template with the QR code base64 data
        return render_template('card.html', qr_code=qr_code_base64, key=key)
    
    except Exception as e:
        print('Error registering user:', e)
        return jsonify([]) 
    
    except Exception as e:
        print('Error registering user:', e)
        return jsonify([])

@app.route('/getUser/<int:card_id>', methods=['GET']) #display buttons
def get_card(card_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE secret = %s", (card_id,))
        card = cur.fetchone()
        cur.close()
        if card:
            return render_template('card-details.html', card=card)
        else:
            return jsonify({'message': 'card not found'})
    except Exception as e:
        print('Error fetching student:', e)
        return jsonify({'message': 'Error fetching card'})

# @app.route('/card-details/<int:card_id>', methods=['GET']) #display details
# def get_card_details(card_id):
#     try:
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE secret = %s", (card_id,))
#         card = cur.fetchone()
#         cur.close()
#         if card:
#             return render_template('card-details.html', card=card)
#         else:
#             return jsonify('no card found')
#     except Exception as e:
#         print('Error fetching card:', e)
#         return jsonify({'message': 'Error fetching card'})
 
@app.route('/admin/<int:card_id>', methods=['GET']) # show admin functions
def admin_access(card_id):
    return render_template('admin.html', card_id=card_id)

@app.route('/api/bus/<int:card_id>', methods=['GET']) # bus ticket
def bus_fare(card_id):
    cur = mysql.connection.cursor()
    cur.execute("select balance from users WHERE secret = %s", (card_id,))
    balance = cur.fetchone()
    if balance[0] is None:
        print("insufficient funds")
        return jsonify('error')
    elif balance[0] < 10:
        print("insufficient funds")
        return jsonify('error')
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users set balance=balance -10 WHERE secret = %s", (card_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify('success')

@app.route('/api/metro/<int:card_id>', methods=['GET']) # metro ticket
def metro_fare(card_id):
    cur = mysql.connection.cursor()
    cur.execute("select balance from users WHERE secret = %s", (card_id,))
    balance = cur.fetchone()
    if balance[0] is None:
        print("insufficient funds")
        return jsonify('error')
    elif balance[0] < 30:
        print("insufficient funds")
        return jsonify('error')
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users set balance=balance -30 WHERE secret = %s", (card_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify('success')

@app.route('/api/toilet/<int:card_id>', methods=['GET']) # toilet ticket
def toilet_fare(card_id):
    cur = mysql.connection.cursor()
    cur.execute("select balance from users WHERE secret = %s", (card_id,))
    balance = cur.fetchone()
    if balance[0] is None:
        print("insufficient funds")
        return jsonify('error')
    elif balance[0] < 3:
        print("insufficient funds")
        return jsonify('error')
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users set balance=balance -3 WHERE secret = %s", (card_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify('success')

if __name__ == '__main__':
    app.run(debug=True)
 