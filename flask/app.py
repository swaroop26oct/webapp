#!/usr/bin/env python3
import sys, psycopg2, os, subprocess, textwrap
from flask import Flask, render_template, request, Markup
from flask.ext.sqlalchemy import SQLAlchemy
from flask import session
app = Flask(__name__)
app.secret_key = "super secret key"
###Section that generates the webpages using templates found in /templates###
#Main page and test page for the template. Do not start the webpage here unless you would like to rename home
#to this
@app.route("/")
def main():
	return render_template('header.html')


@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/basicinfo', methods=['GET', 'POST'])
def basicinfo():
	return render_template('basicinfo.html')

@app.route('/disease', methods=['GET', 'POST'])
def disease():
	if request.method=='POST':
		email = request.form['email']
		#print("email: ", email)
		name = request.form['name']
		#print("name: ", name)
		address = request.form['address']
		#print("address: ", address)
		zipcode = request.form['zipcode']
		zipcode = int(zipcode)
		#print("zip: ", zipcode)
		country = request.form['country']
		#print("country: ", country)
		phone = request.form['phone']
		#print("phone :", phone)
		age = request.form['age']
		age = int(age)
		#print("age :", age)
		sex = request.form['sex']
		#print("sex :", sex)
		height = request.form['height']
		#print("height: ", height)
		weight = request.form['weight']
		weight = int(weight)
		#print("weight: ", weight)
		ethnicity = request.form['radioEthnicity']
		#print("ethnicity: ", ethnicity)
		smoker = request.form['radioSmoker']
		#print("smoker: ", smoker)
		list=[email,name,address,zipcode,country,phone,age,sex,height,weight,ethnicity,smoker]
		conn=connect_user()
		querycmd_user(conn,list)
		conn.close()
		return render_template('disease.html')
	else:
		return render_template('disease.html')


@app.route('/alltrials', methods=['GET', 'POST'])
def alltrials():
	if request.method=='POST':
		disease = request.form['disease']
		session['disease'] = request.form['disease']
		conn2=connect_aact()
		print("Disease: ", disease)
		rows=querycmd_aact(conn2,disease)
		list = []
		for i in rows:
			#edit this for changing the table row content
			line = """<tr><td><a href="https://clinicaltrials.gov/ct2/show/{nct}">{nct}</a></td><td>{title}</td><td>{country}</td></tr>""".format(nct=i[0], title=i[1],country=i[2])
			list.append(line)
		list=''.join(list)
		content = Markup(list)
		return render_template('alltrials.html', content=content)
	else:
		content = Markup("""<tr><td><a href="#">None</a></td><td>None</td></tr>""")
		return render_template('alltrials.html', content=content)
		
@app.route('/location', methods=['GET', 'POST'])
def location():
	if request.method=='POST':
		disease = session['disease']
		loc = request.form['location']
		conn2=connect_aact()
		print("Location: ", loc)
		rows=querycmd_location(conn2,loc,disease)
		list = []
		for i in rows:
			#edit this for changing the table row content
			if (i[2]==loc):
				line = """<tr><td><a href="https://clinicaltrials.gov/ct2/show/{nct}">{nct}</a></td><td>{title}</td><td>{country}</td></tr>""".format(nct=i[0], title=i[1],country=i[2])
				list.append(line)
			else:
				continue
		list=''.join(list)
		content = Markup(list)
		return render_template('location.html', content=content)
	else:
		content = Markup("""<tr><td><a href="#">None</a></td><td>None</td></tr>""")
		return render_template('location.html', content=content)

		
@app.route('/refined', methods=['GET', 'POST'])
def refined():
	if request.method=='POST':
		disease = session['disease']
		conn_local =connect_user()
		country= query(conn_local)
		conn_AACT = connect_AACT()  
		rows = query_refined(conn_AACT,disease,country)
		list = []
		for i in rows:
			line = """<tr><td><a href="https://clinicaltrials.gov/ct2/show/{nct}">{nct}</a></td><td>{title}</td><td>{country}</td><td>{status}</td></tr>""".format(nct=i[0], title=i[1],country=i[2],status=i[3])
			list.append(line)
		list=''.join(list)
		content = Markup(list)
		return render_template('refined.html', content=content)
	else:
		content = Markup("""<tr><td><a href="#">None</a></td><td>None</td></tr>""")
		return render_template('refined.html', content=content)



#Behind the scenes
def connect_user():
	try:
		conn = psycopg2.connect(host='localhost', database= 'ct4me' ,user='postgres', password='October26', port='5432', sslmode='prefer')
	except:
		print("I am unable to connect to the database")
	return conn

def querycmd_user(conn,list):
	cur=conn.cursor()
	query = "INSERT INTO user_detail(email,name,address,zipcode,country,phone,age,sex,height,weight,ethnicity,smoker) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
	value=list
	try:
		cur.execute(query, value)
		conn.commit()
	except:
		print("Cannot execute query...")
	cur.close()

def connect_aact():
	try:
		conn = psycopg2.connect(database='aact', user='aact', password='aact', host='aact-prod.cr4nrslb1lw7.us-east-1.rds.amazonaws.com', port='5432', sslmode='allow')
		print("Connected!")
	except:
		print("I am unable to connect to the database")
	return conn

def connect_AACT():
    try:
        conn_aact = psycopg2.connect(host='localhost', database= 'AACT' ,user='postgres', password='October26', port='5432', sslmode='prefer')
    except:
        print("I am unable to connect to the database")
    return conn_aact

#AACT query
def querycmd_aact(conn,topic):
	cur=conn.cursor()
	subject=topic.split("'")
	subject="''".join(subject)
	query = """
		SELECT DISTINCT k.nct_id, s.brief_title , con.name
			FROM keywords k, studies s,countries con
			WHERE k.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND k.name ILIKE {disease}
			UNION
		SELECT DISTINCT c.nct_id, s.brief_title  ,con.name
			FROM browse_conditions c, studies s , countries con
			WHERE c.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND c.mesh_term  ILIKE  {disease}
			UNION
		SELECT DISTINCT bi.nct_id, s.brief_title , con.name
			FROM browse_interventions bi, studies s , countries con
			WHERE bi.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND bi.mesh_term  ILIKE  {disease}
			UNION
		SELECT DISTINCT i.nct_id, s.brief_title , con.name
			FROM interventions i, studies s, countries con
			WHERE i.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND i.description  ILIKE  {disease}
			UNION
		SELECT DISTINCT dos.nct_id, s.brief_title ,con.name
			FROM design_outcomes dos, studies s, countries con
			WHERE dos.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dos.measure  ILIKE  {disease}
			UNION
		SELECT DISTINCT f.nct_id, s.brief_title , con.name
			FROM facilities f, studies s , countries con
			WHERE f.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND f.name  ILIKE  {disease}
			UNION
		SELECT DISTINCT bs.nct_id, s.brief_title , con.name
			FROM brief_summaries bs, studies s , countries con
			WHERE bs.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND bs.description  ILIKE  {disease} 
			UNION
		SELECT DISTINCT dd.nct_id, s.brief_title , con.name
			FROM detailed_descriptions dd, studies s , countries con
			WHERE dd.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dd.description  ILIKE {disease}
			UNION
		SELECT DISTINCT s.nct_id, s.brief_title ,con.name
			FROM studies s ,countries con
			WHERE s.brief_title ILIKE  {disease}  OR s.official_title ILIKE {disease}
			AND s.nct_id=con.nct_id
			UNION
		SELECT DISTINCT dg.nct_id, s.brief_title , con.name
			FROM design_groups dg, studies s , countries con
			WHERE dg.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dg.title  ILIKE  {disease}
			UNION
		SELECT DISTINCT dw.nct_id, s.brief_title , con.name
			FROM drop_withdrawals dw, studies s ,countries con
			WHERE dw.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dw.reason  ILIKE  {disease}
			UNION
		SELECT DISTINCT om.nct_id, s.brief_title , con.name
			FROM outcome_measurements om, studies s, countries con
			WHERE om.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND om.classification  ILIKE  {disease};
		""".format(disease="'%"+subject+"%'")
	try:
		cur.execute(query)
		conn.commit()
	except:
		print("Cannot execute query...")
	rows = cur.fetchall()
	cur.close()
	return rows


def querycmd_location(conn,loc,disease):
	cur=conn.cursor()
	subject=disease.split("'")
	subject="''".join(subject)
	query = """
		SELECT DISTINCT k.nct_id, s.brief_title , con.name
			FROM keywords k, studies s,countries con
			WHERE k.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND k.name ILIKE {disease}
			UNION
		SELECT DISTINCT c.nct_id, s.brief_title  ,con.name
			FROM browse_conditions c, studies s , countries con
			WHERE c.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND c.mesh_term  ILIKE  {disease}
			UNION
		SELECT DISTINCT bi.nct_id, s.brief_title , con.name
			FROM browse_interventions bi, studies s , countries con
			WHERE bi.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND bi.mesh_term  ILIKE  {disease}
			UNION
		SELECT DISTINCT i.nct_id, s.brief_title , con.name
			FROM interventions i, studies s, countries con
			WHERE i.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND i.description  ILIKE  {disease}
			UNION
		SELECT DISTINCT dos.nct_id, s.brief_title ,con.name
			FROM design_outcomes dos, studies s, countries con
			WHERE dos.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dos.measure  ILIKE  {disease}
			UNION
		SELECT DISTINCT f.nct_id, s.brief_title , con.name
			FROM facilities f, studies s , countries con
			WHERE f.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND f.name  ILIKE  {disease}
			UNION
		SELECT DISTINCT bs.nct_id, s.brief_title , con.name
			FROM brief_summaries bs, studies s , countries con
			WHERE bs.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND bs.description  ILIKE  {disease} 
			UNION
		SELECT DISTINCT dd.nct_id, s.brief_title , con.name
			FROM detailed_descriptions dd, studies s , countries con
			WHERE dd.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dd.description  ILIKE {disease}
			UNION
		SELECT DISTINCT s.nct_id, s.brief_title ,con.name
			FROM studies s ,countries con
			WHERE s.brief_title ILIKE  {disease}  OR s.official_title ILIKE {disease}
			AND s.nct_id=con.nct_id
			UNION
		SELECT DISTINCT dg.nct_id, s.brief_title , con.name
			FROM design_groups dg, studies s , countries con
			WHERE dg.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dg.title  ILIKE  {disease}
			UNION
		SELECT DISTINCT dw.nct_id, s.brief_title , con.name
			FROM drop_withdrawals dw, studies s ,countries con
			WHERE dw.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND dw.reason  ILIKE  {disease}
			UNION
		SELECT DISTINCT om.nct_id, s.brief_title , con.name
			FROM outcome_measurements om, studies s, countries con
			WHERE om.nct_id=s.nct_id
			AND s.nct_id=con.nct_id
			AND om.classification  ILIKE  {disease};
	""".format(disease="'%"+disease+"%'")
	try:
		cur.execute(query)
		conn.commit()
	except:
		print("Cannot execute query...")
	rows = cur.fetchall()
	cur.close()
	return rows

def query(conn_local):
    cur=conn_local.cursor()
    country=""
    query1= ("SELECT country FROM user_detail WHERE  ID=(SELECT MAX(ID) FROM user_detail)")
    try:
        #print("Got till here")
        cur.execute(query1)
    except:
        print("Cannot execute no!!! ! query...")
    data = cur.fetchall()
    for dat in data:
        country=dat[0]
    #print (country)
    return country

def query_refined(conn_AACT,disease_1,country):
    cur=conn_AACT.cursor()
    d=disease_1
    c = country
    trials=[]
    subject = "%"+d+"%"
    query = ("SELECT s.nct_id, s.brief_title,c.name,s.overall_status FROM search_studies ('"+subject+"')ss, studies s,countries c where ss.nct_id=s.nct_id AND s.nct_id=c.nct_id")
    #print(query)
    try:
        cur.execute(query)
    except:
        print("Cannot execute query...")
    rows = cur.fetchall()
    #print (c)
    for row in rows:
        #print (row[1])
        #print (c)
        if (row[2]==c):
            trials.append(row)
        else:
            continue
    #print (trials)
    return trials

if __name__ == '__main__':
	app.run(debug=True)