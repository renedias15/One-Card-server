import io
from flask import Flask, render_template,request,jsonify,redirect
from flask_cors import CORS
from datetime import date,timedelta,datetime
from flask_mysqldb import MySQL
import qrcode
import random
from PIL import Image
import base64
from twilio.rest import Client

account_sid = 'AC9f56c8aa1d9317245bf27259e1352907'
auth_token = 'd5dae385c4d1695aa92116375da10a29'
client = Client(account_sid, auth_token)

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

@app.route('/admin_login')
def admiin_login():
    return render_template('admin_login.html')

@app.route('/instructions')
def instructions():
    return render_template('Instructions.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT count(*) FROM admin WHERE email=%s AND password=%s", (email, password))
    result = cur.fetchone()

    if result[0] > 0:
        # Redirect to the external URL
        return redirect("https://one-card-qr-scanner-fsk3ekx4w-renedias15.vercel.app/")

    # Handle invalid login credentials
    # ...

    return jsonify("Invalid login credentials")  # Or any appropriate response

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
                secret = random.randint(100000000000, 999999999999)
                return check_if_exists(secret)
            else:
                return num

        secret = random.randint(100000000000, 999999999999)
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
    
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        url = 'https://one-card-server.onrender.com/getUser/' + str(key)
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

@app.route('/getUser/<int:card_id>', methods=['GET']) #display card details
def get_card(card_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users where secret = %s", (card_id,))
        card = cur.fetchone()
        cur.close()
        if card:
            return render_template('card-details.html', card=card)
        else:
            return jsonify({'message': 'card not found'})
    except Exception as e:
        print('Error fetching student:', e)
        return jsonify({'message': 'Error fetching card'})
 
@app.route('/admin/<int:card_id>', methods=['GET']) # show admin functions
def admin_access(card_id):
    return render_template('admin.html', card_id=card_id)

############ tickets
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
    else:
        cur = mysql.connection.cursor()
        query="insert into logs (card_id,ticket_type,ticket_cost,date) VALUES (%s,%s,%s,%s)"
        cur.execute(query, (card_id,'bus',10,today))
        mysql.connection.commit()
    
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users set balance=balance -10 WHERE secret = %s", (card_id,))
        mysql.connection.commit()
        cur.close()
        # message = client.messages.create(
        #     body='Bus ticket \n Cost:10 Credits \nThank you for using our service!',
        #     from_='+14027611507',
        #     to='+919049844618'
        # )
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
    else:
        cur = mysql.connection.cursor()
        query="insert into logs (card_id,ticket_type,ticket_cost,date) VALUES (%s,%s,%s,%s)"
        cur.execute(query, (card_id,'metro',30,today))
        mysql.connection.commit()
        
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
    else:
        cur = mysql.connection.cursor()
        query="insert into logs (card_id,ticket_type,ticket_cost,date) VALUES (%s,%s,%s,%s)"
        cur.execute(query, (card_id,'toilet',3,today))
        mysql.connection.commit()
    
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users set balance=balance -3 WHERE secret = %s", (card_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify('success')

###top up button
@app.route('/top-up/<int:card_id>', methods=['GET']) 
def redirects(card_id):
    print("try",card_id)
    return render_template('card_plans.html', card_id=card_id)

###########plans
@app.route('/api/plans/<int:card_id>/<int:plan_id>/<int:validity_days>', methods=['GET']) 
def register_plan(card_id,plan_id,validity_days):
    # print(card_id,plan_id,validity_days)
    # exit()
    expiry_date = date.today() + timedelta(days=validity_days)
    
    cur = mysql.connection.cursor()
    query="insert into selectedPlan (card_id,plan_id,purchase_date,expiry_date,deleted) VALUES (%s,%s,%s,%s)"
    cur.execute(query, (card_id,plan_id,today,expiry_date,0))
    mysql.connection.commit()
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT credits FROM plans WHERE id = %s", (plan_id,))
    res = cur.fetchone()

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET balance = 0 WHERE secret = %s", (card_id,))
    mysql.connection.commit()
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE secret = %s", (res, card_id))
    mysql.connection.commit()
    cur.close()
    
    return jsonify('success')
if __name__ == '__main__':
    app.run(debug=True)
 
