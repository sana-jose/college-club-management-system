import  mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="mypassword",
  database="club_proj"
)
#print(mydb)
cursor=mydb.cursor()

#cursor.execute('''create database if not exists club_proj''')
cursor.execute('''CREATE TABLE if not exists student (
    sid INT PRIMARY KEY,
    f_name VARCHAR(20),
    m_name VARCHAR(20),
    l_name VARCHAR(20),
    email VARCHAR(50),
    batch INT,
    dob DATE,
    status VARCHAR(20) CHECK (status IN ('active', 'inactive')),
    age INT
)''')

cursor.execute('''create table if not exists student_phonenumber(student_id int,phone_number int,primary key(student_id,phone_number))''')
cursor.execute('''create table if not exists clubs(club_id int primary key,clubname varchar(50),por1 varchar(50),por2 varchar(50),faculty varchar(50))''')
cursor.execute('''create table if not exists teams(team_id int ,club_id int ,name varchar(50),primary key(team_id,club_id))''')
cursor.execute('''create table if not exists projects(project_id int ,student_id int,project_name varchar(50),club_id int,primary key(project_id,club_id))''')
cursor.execute('''create table if not exists events(event_id int,club_id int,event_name varchar(50),event_loc varchar(50),date_of_event date,primary key(event_id,club_id))''')
cursor.execute('''create table if not exists student_events(event_name varchar(50),student_id int,role varchar(30),club_id int,event_id int,primary key(student_id,event_id))''')
cursor.execute('''create table if not exists notice(notice_id int,notice_body varchar(500),notice_date date,club_id int,primary key(notice_id,club_id))''')
cursor.execute('''create table if not exists student_team (student_id int,team_id int,club_id int,primary key(student_id,team_id,club_id))''')
