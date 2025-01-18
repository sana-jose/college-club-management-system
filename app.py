from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify 
import mysql.connector
import regex as re
from datetime import date

credentials = mysql.connector.connect(
  host="localhost",
  user="root",
  password="mypassword",
  database="credentials"
)

project=mysql.connector.connect(
    host="localhost",
    user="root",
    password="mypassword",
    database="club_proj"
)

cursor=project.cursor()
cred_cursor=credentials.cursor()


app=Flask(__name__)
app.secret_key = 'your secret key'
@app.route('/', methods=['GET', 'POST'])
def login():
    msg=' '
    if request.method=='POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cred_cursor.execute("select * from cred where username= %s and password=%s",(username, password, ))
        account=cred_cursor.fetchone()
        if account:
            #email=account[1]
            id=account[0]
            session['student_id'] = id

            #global_username=id
            #print(id)
            msg='logged in successfully'
            cursor.execute('''select * from student_team where student_id=%s''',(id,))
            student=cursor.fetchall()
            clubs=list({row[2] for row in student})
            teams=[row[1] for row in student]
            club_team=[[row[1], row[2]] for row in student]
            clubnames=[]
            for club in clubs:
                cursor.execute('''select clubname from clubs where club_id=%s''',(club, ))
                name=cursor.fetchone()
                clubnames.append(name[0])
            
            print(clubnames)
            print(club_team)
            #print(clubs)
            #print(teams)
            #print(student)
            return render_template('index.html', msg=msg, clubnames=clubnames)
        else:
            msg='Incorrect password/username'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    msg=''
    if request.method == 'POST' and all(field in request.form for field in ['username', 'password', 'email', 'first_name', 'last_name', 'phone1', 'batch']): 
        username=request.form['username']#let this be the id number
        password=request.form['password']    
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name')  # Optional field
        last_name = request.form['last_name']
        phone1 = request.form['phone1']
        phone = request.form.get('phone')  # Optional field
        batch = request.form['batch']
        email=request.form['email']
        cred_cursor.execute("select * from cred where username= %s and password=%s",(username, password, ))
        account=cred_cursor.fetchone()
        
        if account:
            msg="account already exists!!"
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg='invalid email'
            id=email[1:9]
        elif phone and not re.match(r'\d+', phone):
            msg='phone number must contain only digits'
        elif phone1 and not re.match(r'\d+', phone):
            msg='phone number must contain only digits'
        elif not username or not password or not email or not first_name or not last_name or not phone1 or not batch:
            msg = 'Please fill out the form !'
        
        else:
            cred_cursor.execute('''INSERT INTO cred (username, password) VALUES (%s, %s)''', (email[1:9], password))
            cursor.execute(
    '''
    INSERT INTO student (sid, f_name, m_name, l_name, email, batch, dob, status, age)
    VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL)
    ''',
    (email[1:9], first_name, middle_name, last_name, email, batch)
)
            credentials.commit()
            project.commit()
            msg='you have successfully registered'
    elif request.method=='POST':
        msg='pls fill out the form'


    return render_template('register.html', msg = msg)


@app.route('/club/<club_name>')
def club_details(club_name):
    cursor.execute('''select club_id from clubs where clubname=%s''',(club_name, ))
    club_id=cursor.fetchone()[0]
    session['club_id']=club_id
    print(club_id)
    id=session.get('student_id')
    cursor.execute('''select notice_body, notice_date from notice where club_id=%s order by notice_date DESC''',(club_id, ))
    notices=cursor.fetchall()
    notice1=notices[::-1]
    #print(notices)
    cursor.execute('''select project_name from projects where student_id=%s and club_id=%s''',(id, club_id, ))
    projects=cursor.fetchall()
    #print("projects=", [project for project in projects])
    cursor.execute('''select event_name, date_of_event from events where club_id=%s order by date_of_event ASC''', (club_id,))
    events = cursor.fetchall()
    return render_template('club_details.html', club_name=club_name, notices=notice1, projects=projects, events=events)



@app.route('/add-club', methods=['GET', 'POST'])
def join_club():
    if request.method == 'POST':
        student_id = session.get('student_id') 
        club_id = request.form['club_id']
        team_id = request.form['team_id']
        
        if not club_id or not team_id:
            flash("Please select both a club and a team.")
            return redirect(url_for('join_club'))

        try:
            cursor.execute('''INSERT INTO student_team (student_id, team_id, club_id) 
                              VALUES (%s, %s, %s)''', (student_id, team_id, club_id))
            project.commit()

            flash("You have successfully joined the club!")
        except Exception as e:
            flash(f"Error: {e}")
        return redirect('index_page')

    cursor.execute('''SELECT club_id, clubname FROM clubs''')
    clubs = cursor.fetchall()

    return render_template('join_club.html', clubs=clubs)


@app.route('/get_teams/<int:club_id>')
def get_teams(club_id):
    try:
        cursor.execute('''SELECT team_id, name FROM teams WHERE club_id = %s''', (club_id,))
        teams = cursor.fetchall()

        if not teams:
            #print(f"No teams found for club_id: {club_id}")  
            return jsonify([])  
        #print(f"Teams found for club_id {club_id}: {teams}")
        teams_list = [{'team_id': team[0], 'name': team[1]} for team in teams] 
        return jsonify(teams_list)
    except Exception as e:
        print(f"Error fetching teams: {e}") 
        return jsonify({'error': 'Failed to fetch teams'})



@app.route('/add_notice', methods=['GET', 'POST'])
def add_notice():
    clubid=session.get('club_id')
    #print(clubid)
    student_id=session.get('student_id')
    cursor.execute('''select f_name, m_name, l_name from student where sid=%s''',(student_id, ))
    student_name=cursor.fetchall()[0]
    name=""
    for n in student_name:
        if n is not None:
            name+=n+' '
    print(name)
    cursor.callproc('CanUploadNotice', [name, clubid])
    for result in cursor.stored_results():
        final_result=(result.fetchall()[0][0])
    if final_result=='Authorized':
        #add functionality for next page
         return redirect(url_for('add_notice_form'))
    else:
        return "<h1>Unauthorized</h1>", 403



@app.route('/add_notice_form', methods=['GET'])
def add_notice_form():
    return render_template('notice_form.html')


@app.route('/view_members', methods=['GET'])
def view_members():
    clubid=session.get('club_id')
    #print(clubid)
    student_id=session.get('student_id')
    cursor.execute('''select f_name, m_name, l_name from student where sid=%s''',(student_id, ))
    student_name=cursor.fetchall()[0]
    name=""
    for n in student_name:
        if n is not None:
            name+=n+' '
    print(name)
    cursor.callproc('CanUploadNotice', [name, clubid])
    for result in cursor.stored_results():
        final_result=(result.fetchall()[0][0])
    if final_result=='Authorized':
        return redirect(url_for('view_members_notinteams'))
    else:
        return "<h1>Unauthorized</h1>", 403

#complex query1
@app.route('/view_members_notinteams')
def view_members_notinteams():
    club_id = session.get('club_id')
    cursor.execute('''
        SELECT s.f_name, s.m_name, s.l_name, sp.phone_number
        FROM student s
        LEFT JOIN student_team st ON s.sid = st.student_id
        LEFT JOIN student_phonenumber sp ON s.sid = sp.student_id
        LEFT JOIN projects p ON s.sid = p.student_id
        WHERE st.team_id IS NOT NULL 
          AND st.club_id = %s 
          AND p.project_id IS NULL
    ''', (club_id,))
    members = cursor.fetchall()
    return render_template('view_members.html', members=members)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    clubid=session.get('club_id')
    cursor.execute('''select clubname from clubs where club_id=%s''',(clubid,))
    clubname=cursor.fetchone()[0]

    return redirect(url_for('club_details', club_name=clubname))

@app.route('/index', methods=['GET'])
def index_page():
    student_id=session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))
    msg='welcome back'
    cursor.execute('''select * from student_team where student_id=%s''',(student_id,))
    student=cursor.fetchall()
    clubs=list({row[2] for row in student})
    teams=[row[1] for row in student]
    club_team=[[row[1], row[2]] for row in student]
    clubnames=[]
    for club in clubs:
        cursor.execute('''select clubname from clubs where club_id=%s''',(club, ))
        name=cursor.fetchone()
        clubnames.append(name[0])
    
    print(clubnames)
    print(club_team)
    #print(clubs)
    #print(teams)
    #print(student)
    return render_template('index.html', msg=msg, clubnames=clubnames)





@app.route('/submit_notice', methods=['POST'])
def submit_notice():
    notice_body = request.form.get('notice_body')
    club_id = session.get('club_id')
    if not notice_body:
        print('notice_body missing')
    cursor.execute('''insert into notice (notice_body, notice_date, club_id) values(%s, %s, %s)''',(notice_body, date.today(), club_id,))
    project.commit()
    return redirect(url_for('index_page'))

#complex query2
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    query = '''
        SELECT 
            student.sid,
            student.f_name,
            student.l_name,
            COUNT(student_events.event_id) AS participation_count
        FROM 
            student
        JOIN 
            student_events ON student.sid = student_events.student_id
        GROUP BY 
            student.sid, student.f_name, student.l_name
        ORDER BY 
            participation_count DESC
        LIMIT 5;
        '''
    cursor.execute(query)
    result=cursor.fetchall()
    students = [{"sid": row[0], "first_name": row[1], "last_name": row[2], "participation_count": row[3]} for row in result]
    return render_template('leaderboard.html', students=students)
    
#complex query3
@app.route('/view_unaffiliated_participants')
def view_unaffiliated_participants():
    club_id = session.get('club_id')
    student_id = session.get('student_id')
    cursor.execute('''select f_name, m_name, l_name from student where sid=%s''',(student_id, ))
    student_name=cursor.fetchall()[0]
    name=""
    for n in student_name:
        if n is not None:
            name+=n+' '
    print(name)
    cursor.callproc('CanUploadNotice', [name, club_id])
    for result in cursor.stored_results():
        final_result=(result.fetchall()[0][0])
    if final_result=='Authorized':
        query = '''
    SELECT c.clubname, COUNT(DISTINCT se.student_id) AS unique_participants
    FROM clubs c
    JOIN events e ON c.club_id = e.club_id
    JOIN student_events se ON e.event_id = se.event_id
    JOIN student_team st ON se.student_id = st.student_id
    WHERE st.team_id NOT IN (
        SELECT t.team_id
        FROM teams t
        WHERE t.club_id = c.club_id
    )
    GROUP BY c.clubname
    ORDER BY unique_participants DESC;
    '''
        cursor.execute(query)
        results = cursor.fetchall()
        return render_template('unaffiliated_participants.html', results=results)

#complex query4
@app.route('/view_external_participants')
def view_external_participants():
    student_id = session.get('student_id')
    club_id = session.get('club_id')
    cursor.execute('''SELECT f_name, m_name, l_name FROM student WHERE sid=%s''', (student_id,))
    student_name = cursor.fetchall()[0]
    name = " ".join([n for n in student_name if n is not None])
    cursor.callproc('CanUploadNotice', [name, club_id])
    
    for result in cursor.stored_results():
        final_result = (result.fetchall()[0][0])
    
    if final_result != 'Authorized':
        return "<h1>Unauthorized</h1>", 403
    
    # Execute the main query
    query = '''
    SELECT 
        student.sid,
        student.f_name,
        student.l_name
    FROM 
        student
    JOIN 
        student_events ON student.sid = student_events.student_id
    JOIN 
        student_team ON student.sid = student_team.student_id
    WHERE
        student_events.event_id NOT IN (
            SELECT e.event_id
            FROM events e
            JOIN teams t ON e.club_id = t.club_id
            WHERE t.team_id IN (
                SELECT st.team_id
                FROM student_team st
                WHERE st.student_id = student.sid
            )
        )
    GROUP BY
        student.sid, student.f_name, student.l_name
    HAVING
        COUNT(DISTINCT student_events.event_id) >= 1;
    '''
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    participants = [{"sid": row[0], "first_name": row[1], "last_name": row[2]} for row in results]
    return render_template('external_participants.html', participants=participants)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        event_loc = request.form['event_location']  # Use event_loc to match your table column
        club_id = session.get('club_id')

        if not event_name or not event_date or not event_loc:
            flash("All fields are required!")
            return redirect(url_for('add_event'))

        try:
            print(f"Executing query: INSERT INTO events (club_id, event_name, event_loc, date_of_event) VALUES ({club_id}, {event_name}, {event_loc}, {event_date})")
            cursor.execute('''
                INSERT INTO events (club_id, event_name, event_loc, date_of_event)
                VALUES (%s, %s, %s, %s)
            ''', (club_id, event_name, event_loc, event_date, ))
            project.commit()  # Commit the transaction
            flash("Event added successfully!")
            return redirect(url_for('index_page'))
        except Exception as e:
            flash(f"Database Error: {e}")
            project.rollback()  # Roll back in case of error
            return redirect(url_for('add_event'))

    # Render the form for GET requests
    return render_template('add_event.html')

if __name__=="__main__":
    app.run(debug=True)