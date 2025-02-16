from flask import url_for, render_template, make_response
from app import db, mail
from flask_jwt_extended import create_access_token
from flask_mail import Message
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime
import secrets, base64

def register_user(data):
    fullname = data['fullname']
    email = data['email']
    no_hp = data['no_hp']
    gender = data ['gender']
    password = data['password']
    confirm_password = data['confirm_password']
    default_photo = "https://res.cloudinary.com/dohsfgda5/image/upload/v1718499502/pbw0rkfl8kz2gklvwlbz.jpg"
    datetime_now = datetime.now().strftime("%Y%m%d%H%M%S")
    verification_token = secrets.token_urlsafe(32)
    
    # Confirmation Password Check
    if password != confirm_password:
        return {
            'message': 'Password tidak cocok, cek kembali password nya!'
        }, 400
        
    # Check Email Already Registered
    user = db.db.users.find_one({"email": email})
    if user:
        return {
            'message': 'Email ini telah terdaftar sebelumnya, gunakan email yang lain!'
        }, 400
        
    hashed_password = PasswordHasher().hash(password)
    
    try:
        user = {
            "fullname": fullname,
            "email": email,
            "no_hp": no_hp,
            "password": hashed_password,
            "photo": default_photo,
            "gender": gender,
            "is_verify": False,
            "created_at": datetime_now,
            "updated_at": datetime_now,
        }
        
        token = {
            "email": email,
            "token": verification_token
        }
        
        result = db.db.users.insert_one(user)
        result = db.db.token.insert_one(token)
        
        confirmation_url = url_for('auth.verify_account', token=verification_token, _external=True)
        
        data = {
            'name': fullname,
            "url": confirmation_url
        }
        
        msg = Message(subject="Verify Your Email - SpineMotion", sender="spinemotionapp@gmail.com", recipients=[email])
        msg.html = render_template("verify-email.html", data=data)
        
        mail.send(msg)
                
        return {
            "message": "Berhasil mendaftar, cek email untuk verifikasi"
        }, 201
    
    except Exception as e:
        return {
            "message": f"Error {e}"
        }, 500

def verif_user(token):
    try:
        token = db.db.token.find_one({"token": token})
        if not token:
            response = make_response(render_template('response.html', success=True, message='Account has ben verified'), 400)
            response.headers['Content-Type'] = 'text/html'
            return response
        
        email = token["email"]
        user = db.db.users.find_one({"email": email})
        
        if user["is_verify"] == True:
            response = make_response(render_template('response.html', success=False, message='Account has been verified'), 400)
            response.headers['Content-Type'] = 'text/html' 
            return response

        update_data = {"is_verify" : True}
        db.db.users.update_one({"email": email}, {"$set": update_data})
        
        response = make_response(render_template('response.html', success=True, message='Account has ben verified'), 400)
        response.headers['Content-Type'] = 'text/html'
        
        db.db.token.delete_one({"token": token})
        
        return response
    
    except Exception as e:
        return {"message": f"Error {e}"}, 500

def login_user(data):
    base64Str = data[6:] # hapus "Basic" string
    
    #Mulai Base64 Decode
    base64Bytes = base64Str.encode('ascii')
    messageBytes = base64.b64decode(base64Bytes)
    pair = messageBytes.decode('ascii')
    #Akhir Base64 Decode
    
    email, password = pair.split(":")
    
    user = db.db.users.find_one({"email": email})
    
    if not user:
        return {
            "message": "Pengguna tidak ditemukan, silahkan register terlebih dahulu"
        }, 400
    
    if user["is_verify"] == False:
        return {
            "message": "Pengguna berlum terverifikasi, silahkan cek email"
        }
    
    try:
        if PasswordHasher().verify(user["password"], password):
            payload = {
                'id': str(user["_id"]),
                'email': user["email"],
                'fullname': user["fullname"]
            }
                
            token = create_access_token(identity=email)
                
            return {'message': 'Berhasil login',
                        'user': payload,
                        'token': token 
                        }, 200
        else:
            return { 'message': 'Password salah' }, 401
    except VerifyMismatchError:
        return { 'message': 'Password tidak sesuai' }, 401
