from datetime import datetime
from app import db, mail
import secrets, random
from flask_mail import Message
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import url_for, render_template, make_response, render_template_string
from flask_jwt_extended import get_jwt_identity

def get_profile(email):
    try:
        user = db.db.users.find_one({"email": email})
    
        if not user:
            return {
                'message': 'Pengguna tidak ditemukan'
            }, 404
            
        return {
            'message': 'success',
            'data': {
                'id': str(user["_id"]),
                'fullname': user["fullname"],
                'email': user["email"],
                'no_hp': user["no_hp"],
                'photo': user["photo"],
            }
        }, 200
    
    except Exception as e:
        return {'message' : f"Error {e}"}, 500
    

def forgot_password_user(data):
    try:
        email = data["email"]
    
        user = db.db.users.find_one({"email": email})
        
        if not user:
            return {
                "message": "Email tidak terdaftar"
            }, 404
        
        verification_token = secrets.token_urlsafe(32)
        
        token = {
            "email": email,
            "token": verification_token
        }
        
        db.db.token.insert_one(token)
        
        confirmation_url = url_for('user.reset_password_view', token=verification_token, _external=True)
        
        msg = Message(subject="Reser Your Password - SpineMotion", sender="spinemotionapp@gmail.com", recipients=[email])
        msg.html = render_template("reset-password.html", url=confirmation_url)
        
        mail.send(msg)
        
        return {'message' : "Berhasil meminta reset password, silahkan cek email"}, 200
    
    except Exception as e:
        return {'message' : f"Error {e}"}, 500
    
def reset_password_view_user(token):
    try:
        token = db.db.token.find_one({"token": token})
        if not token:
            return {
                'message':'Token not found'
            }, 404
        
        email = token["email"]
        user = db.db.users.find_one({"email": email})
        if not user:
            return {
                "message": "User not found"
            }, 404
        
        response = make_response(render_template('form-reset-password.html', email=user["email"]), 200)
        response.headers["Content-Type"] = "text/html"
        return response
    except Exception as e:
        return {
            "message": f"Error {e}"
        }, 500

def reset_password_user(password, confirm_password, email):
    try:
        user = db.db.users.find_one({"email": email})
        
        if not user:
            return {
                "message": "Pengguna tidak ditemukan"
            }, 404
            
        if password != confirm_password:
            return {
                "message": "Password tidak sesuai"
            }
        
        new_password = PasswordHasher().hash(password)
        
        update_password = {
            "password": new_password
        }
        
        try:
            db.db.users.update_one({"email": email}, {"$set": update_password})
            db.db.token.delete_one({"email": email})
            response = make_response(render_template('response.html', success=True, message='Password has been reset successfully'), 200)
            response.headers['Content-Type'] = 'text/html'
            return response
        
        except:    
            response = make_response(render_template('response.html', success=False, message='Reset password failed'), 400)
            response.headers['Content-Type'] = 'text/html'
            return response
    except Exception as e:
        return {
            "message": f"Error {e}"
        }, 500
        
def change_password_user(data):
    old_password = data["oldPassword"]
    password = data["password"]
    confirm_password = data["confirmPassword"]
    email = get_jwt_identity()
    
    user = db.db.users.find_one({"email": email})
    try:
        if PasswordHasher().verify(user["password"], old_password):
            if password != confirm_password:
                return {
                    "message": "Password baru tidak cocok, cek kembali password nya!"
                }, 401
            
            # Hash password baru
            new_password_hashed = PasswordHasher().hash(password)
            
            # simpan password baru
            update_password = {
                "password": new_password_hashed
            }
            
            db.db.users.update_one({"email": email}, {"$set": update_password})
            
            return {
                "message": "Berhasil mengubah password"
            }, 200
    except VerifyMismatchError:
        return {
            "message": "Password lama tidak sesuai"
        }, 401
    return "change pws"

def request_change_email_service(data):
    email = get_jwt_identity()
    new_email = data["new_email"]
    password = data["password"]
    
    user = db.db.users.find_one({"email": email})
    
    if not user:
        return {
            "message": "Pengguna tidak ditemukan, silahkan register terlebih dahulu"
        }, 400
        
    try:
        if PasswordHasher().verify(user["password"], password):
                       
            otp = random.randint(100000, 999999)
            
            created_at = datetime.now().strftime("%Y%m%d%H%M%S")
            
            data = {
                "name": user["fullname"],
                "otp": otp
            }  
            
            input_otp = {
                "email": email,
                "new_email": new_email,
                "otp": str(otp),
                "created_at": created_at
            }
            
            db.db.otp_change_email.insert_one(input_otp)
            
            msg = Message(subject="OTP to Verify New Email - Spinemotion", sender="spinemotionapp@gmail.com", recipients=[new_email])
            msg.html = render_template("verify-change-email.html", data=data)
            mail.send(msg)
            
            return {
                'message': "Berhasil request, cek email yang baru untuk lihat kode OTP"
            }, 200
        else:
            return { 'message': 'Password salah' }, 401
    except VerifyMismatchError:
        return { 'message': 'Password tidak sesuai' }, 401
    
def verify_otp_service(data):    
    otp = data["otp"]
    
    data_otp = db.db.otp_change_email.find_one({"otp": otp})
    
    if not data_otp:
        return {
            "message": "otp tidak sesuai"
        }, 400
    
    old_email = data_otp["email"]
    new_email = data_otp["new_email"]
    
    update_email = {
        "email": new_email
    }
    
    db.db.users.update_one({"email": old_email}, {"$set": update_email})
    db.db.otp_change_email.delete_one({"otp": otp})
    
    return {
        "message": "Email berhasil diubah"
    }, 200
    
def update_profile_service(data, files):
    email = get_jwt_identity()
    user = db.db.users.find_one({"email": email})
    
    if not user:
        return {
            "message": "Pengguna tidak ditemukan"
        }, 404
    
    try:
        updates = {}
        if files:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_image.jpg"
            path = f"static/uploads/profiles/{filename}"
            files.save(path)
            updates["photo"] = filename
        
        if "fullname" in data:
            updates["fullname"] = data["fullname"]
            
        if "no_hp" in data:
            updates["no_hp"] = data["no_hp"]
            
        if updates:
            db.db.users.update_one({"email": email}, {"$set": updates})
            
        return {
            "message": "Berhasil update profil"
        }
    except Exception as e:
        return {
            "message": f"Error {e}"
        }, 500
        
def perform_service(email):
    id = str(db.db.users.find_one({"email": email})["_id"])
    name = db.db.users.find_one({"email": email})["fullname"]
    return render_template_string(f'''
        <!doctype html>
        <iframe src="http://192.168.40.107:8501/?user_id={id}&name={name}" width="100%" height="2000"></iframe>
    ''')