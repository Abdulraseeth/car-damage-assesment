from cloudant.client import Cloudant

client = Cloudant.iam('92de3d5a-b233-40e8-9867-e28c6da4a158-bluemix', 'HYQkCEhYDPRe95gguUkvpsTV6r2wiGj2pbtb8UtVRKXf', connect=True)
my_database=client['my_database']

import numpy as np
import os
from flask import Flask, app,request,render_template,redirect,url_for,session,flash
from tensorflow.keras import models
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from cloudant.query import Query
import smtplib

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.applications.inception_v3 import preprocess_input
import requests
import webbrowser

os.add_dll_directory

model1=load_model(r'C:\Users\Asus\Desktop\My PG Project\FinalYear Project\Final Project\Model\body.h5')
model2=load_model(r'C:\Users\Asus\Desktop\My PG Project\FinalYear Project\Final Project\Model\level.h5')
model3=load_model(r'C:\Users\Asus\Desktop\My PG Project\FinalYear Project\Final Project\Model\car.h5',compile=False)


app=Flask(__name__)
app.secret_key = 'abdras123'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def home():
    return render_template("index.html")

@app.route('/register.html')
def register():
    return render_template("register.html")

@app.route('/afterreg',methods=['POST'])
def afterreg():
    x = [x for x in request.form.values()]
    hashed_psw = generate_password_hash(x[2], method='pbkdf2:sha256')
    data={'_id':x[1],'name':x[0],'psw':hashed_psw} 
    print(data)
    query={'_id':{'$eq':data['_id']}}   
    docs=my_database.get_query_result(query)
    print(docs)
    if (len(docs.all())==0):
        url=my_database.create_document(data)
        send_emailreg(x[1],x[2])
        return render_template("login.html",pred="Registration Successful. Details sent to your mail. Please login with your registered details.")
    else:
        return render_template("login.html",pred="You are already a member! Please login using your registered details.")

@app.route('/login.html')
def login():
    return render_template("login.html")

@app.route('/afterlogin',methods=['POST'])
def afterlogin():
    user=request.form['_id']
    passw=request.form['psw']
    query={'_id':{'$eq':user}}
    docs=my_database.get_query_result(query)
    print(docs)
    if (len(docs.all())==0):
        return render_template("login.html",pred="The mail is not found! Please enter registered mail ID or register with a new one.")
    else:
        if check_password_hash(docs[0][0]['psw'], passw):
            session['_id'] = user
            return redirect(url_for('prediction'))
        else:
            return render_template("login.html",pred="The password is incorrect! Please login with correct password.")

@app.route('/forgot.html',methods=['GET','POST'])
def forgot():
    return render_template("forgot.html")

@app.route('/afterforgot',methods=['GET','POST'])
def afterforgot():
    user = request.form['_id']
    passw1=request.form['psw1']
    passw2=request.form['psw2']

    if user in my_database:
        if (passw1)!= (passw2):
            return render_template("forgot.html",pred="Passwords do not match! Please try again.")
        user_doc = my_database[user]
        hashed_psw = generate_password_hash(passw1, method='pbkdf2:sha256')
        user_doc['psw'] = hashed_psw
        send_email(user, passw1)
        user_doc.save()
        return render_template("forgot.html",pred="Password updated successfuly : ) Details sent to your mail. Please login with new password.")
    else:
        return render_template("forgot.html",pred="Mail not found! Please enter correct Mail ID.")
    
def send_email(user, passw1):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('abdulraseeth04@gmail.com', 'cjhqhxwccgrhckfo')
    message = 'Subject: New Password for our Car Damage Assessment Portal\n\nYour new password is: ' + passw1+'. Please login using this new password. ' 
    server.sendmail('abdulraseeth04@gmail.com', user, message)
    server.quit()

def send_emailreg(user, passw):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('abdulraseeth04@gmail.com', 'cjhqhxwccgrhckfo')
    message = 'Subject: Registration Success\n\nThanks for registering into our Car Damage Assessment Portal. Your mail is: ' + user + '\nYour Password is: ' +passw
    server.sendmail('abdulraseeth04@gmail.com', user, message)
    server.quit()
   
@app.route('/logout.html')
def logout():
    session.clear()
    return render_template("logout.html")

@app.route('/prediction.html')
def prediction():
    if '_id' in session:
        return render_template("prediction.html")
    else:
        return render_template("login.html",pred="Please login first before accessing the prediction page!")

@app.route('/result',methods=["GET","POST"])
def result():
    if request.method=="POST":
        f=request.files['file']
        cost=request.form['cost']
        y=(int)(cost)/1000000
        filename = secure_filename(f.filename)
        filename = filename.replace(' ', '_')
        print(filename)
        filepath=os.path.join('static','uploads', filename)
        f.save(filepath)
        img=image.load_img(filepath,target_size=(256, 256))
        x=image.img_to_array(img)
        x=np.expand_dims(x,axis=0)
        img_data=preprocess_input(x)
        prediction3=model3.predict(img_data)
        print(prediction3)
        if prediction3[0][0] < 0.7:
           print(filename)
           return render_template("result.html",filename=filename, prediction="Please upload a car image!")
        else:
            prediction1=np.argmax(model1.predict(img_data))
            prediction2=np.argmax(model2.predict(img_data))
            index1=['front','rear','side']
            index2=['minor','moderate','severe']
            result1=index1[prediction1]
            result2=index2[prediction2]
            print(result1)
            print(result2)
            if(result1=="front"and result2=="minor"):
                value="3000 - 9000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="front"and result2=="moderate"):
                value="8000 - 16000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="front"and result2=="severe"):
                value="15000 - 25000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="rear"and result2=="minor"):
                value="3000 - 10000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="rear"and result2=="moderate"):
                value="9000 - 18000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="rear"and result2=="severe"):
                value="17000 - 30000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="side"and result2=="minor"):
                value="5000 - 13000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="side"and result2=="moderate"):
                value="12000 - 24000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            elif(result1=="side"and result2=="severe"):
                value="23000 - 40000"
                value_range = value.split(" - ")
                range_min = int(value_range[0]) * y
                range_max = int(value_range[1]) * y
                value = "{:.0f} - {:.0f} INR".format(range_min, range_max)
            else:
                value="40000 - 80000 INR"
            return render_template("result.html",filename=filename ,prediction="Estimated cost for the damage is: ₹ "+value+"( "+result1+" , "+result2+" )")
url='http://127.0.0.1:8080'

if __name__=="__main__":
    webbrowser.open_new_tab(url)
    app.run(debug=False,port=8080)

