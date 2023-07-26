from flask import Flask, request, render_template, redirect, flash
import dynamodb_handler as dynamodb
import os
import boto3



app = Flask(__name__)

aws_secret_access_key = ''
aws_access_key_id     = ''
app.secret_key = os.urandom(16)
s3_bucket_name = ''


s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signup', methods=['POST'])
def add_signup():
    data = request.form.to_dict()

    # Process image upload
    profile_photo = request.files['profile_photo']
    if profile_photo:
        # Save the image to S3
        s3.upload_fileobj(profile_photo, s3_bucket_name, profile_photo.filename)
        data['profile_photo'] = profile_photo.filename

    response = dynamodb.add_item_to_student_table(
        data['fname'], data['regNo'], data['email'], data['password'], data['degree'], data['contact'],
        data['introduction'], data['gpa'], data['skills'], data['profile_photo']
    )
    
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return redirect('/login')
    
    return {  
        'msg': 'Some error occurred',
        'response': response
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = dynamodb.get_student_from_table(email)

        if user and user['password'] == password:
            return redirect('/profile-view?email=' + email)
        else:
            flash('Invalid email or password. Please try again.')

    return render_template('login.html')


@app.route('/profile-view')
def profile_view():
    email = request.args.get('email')

    user = dynamodb.get_student_from_table(email)

    if user:
        return render_template('profile-view.html', student_data=user)
    else:
        flash('User not found.')

    return redirect('/login')
    
    
@app.route('/profile-update', methods=['GET', 'POST'])
def profile_update():
    email = request.args.get('email')

    user = dynamodb.get_student_from_table(email)

    if user is None:
        flash('User not found.')
        return redirect('/profile-view?email=' + str(email) if email else '/profile-view')

    if request.method == 'POST':
        data = request.form.to_dict()

        response = dynamodb.update_item_in_student_table(user['regNo'], data)

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            # Update successful, fetch the updated user data
            updated_user = dynamodb.get_student_by_regNo(user['regNo'])
            return render_template('profile-view.html', student_data=updated_user)
        else:
            flash('Failed to update profile. Please try again.')

    if 'cancel' in request.form:
        return redirect('/profile-view?email=' + str(email) if email else '/profile-view')

    return render_template('profile-update.html', student_data=user)




    
@app.route('/profile-delete', methods=['POST'])
def profile_delete():
    regNo = request.form.get('regNo')

    if regNo is not None:
        try:
            regNo = int(regNo)

            response = dynamodb.delete_item_from_student_table(regNo)

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                flash('Profile deleted successfully.')
            else:
                flash('Failed to delete profile. Please try again.')

        except ValueError:
            flash('Invalid regNo value. Please enter a valid number.')

    else:
        flash('Missing regNo value. Please provide a regNo.')

    return redirect('/')





if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
