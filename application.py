
from flask import Flask
from flask import flash, render_template, request, redirect, url_for
from wtforms import Form, StringField, SelectField
import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask import g 
#from SQLAlchemy import create_engine
class DescriptionSearch(Form):
    choices = ['Default','All Sources']
    select = SelectField('Search specification:', choices=choices)
    search = StringField('')
urls = []

url = ""

def lower_upper(table_name):
    temp = ""
    for x in range(len(table_name)):
        if x != 0:
            if table_name[x-1].islower() and table_name[x].isupper():
                 temp = temp + " | "
        temp = temp + table_name[x]
    return temp
def get_workbench(table_name):
    global url
    base_url = "https://dev-workbench.com/en/sap-dictionary/table/"
    url = base_url + table_name
    #compare b504 diff webs
    response = requests.get(url,
    headers = {
        'User-Agent': 'Popular browser\'s user-agent',
        }
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    description = soup.title.string
    if(description == "Redirecting to https://dev-workbench.com/en"):
        return "NA"
    
    return description
    
def get_tcode(table_name):
    global url
    base_url = "https://www.tcodesearch.com/sap-tables/"
    url = base_url + table_name
    
    response = requests.get(url,
    headers = {
        'User-Agent': 'Popular browser\'s user-agent',
        }
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    
    if(soup.title.string == "The page you were looking for doesn't exist (404)"):
        return "NA"
    
    return soup.title.string
def get_trailsap(table_name):
    global url
    base_url = "https://www.trailsap.com/sap/?sap-table="
    url = base_url + table_name
    
    response = requests.get(url,
    headers = {
        'User-Agent': 'Popular browser\'s user-agent',
        }
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    if(soup.title.string == "List of SAP Tables beginning with "+ table_name.upper()):
        return "NA"
    
    return soup.title.string
def get_jde(table_name):
    global url
    base_url = "https://jde.erpref.com/?schema=910&table="
    url = base_url + table_name
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    description = soup.find('tr', class_='odd')
    #description = soup.find('td', class_='syshead') Report
    if description:
        description = description.text.strip()
        
        return lower_upper(description[14:])
    else:
        return "NA"
def get_se80(table_name):
    global url
    base_url = "https://www.se80.co.uk/sap-tables/?name="
    url = base_url + table_name
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    description = soup.title.string
    if(description == " SAP table not found - SAP Help" or description == " 404 Page not found - SAP Help"):
        return "NA"
    
    return description

def get_leanx(table_name):
    print("start")
    global url
    base_url = "https://leanx.eu/en/sap/table/"
    url = base_url + table_name
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    description = soup.find('li', class_='active')
    if(description):
        description = description.text.strip()

        #return description[(len(table_name)+3):]
        if(description == "-"):
            return "NA"
    
        return description
    else:
        return "NA"
        
def contains_invalid_ascii(table_name):
    for letter in table_name:
        asc = ord(letter)
        if(not ((asc >= 65 and asc <= 90) or (asc >= 97 and asc <= 122) or asc == 95 or asc == 47 or (asc >= 48 and asc <= 57))):
            return(True)
    return(False)


funcs = [get_leanx,get_workbench,get_tcode,get_jde,get_se80,get_trailsap]
def get_descriptions(table_name):
    descs = []
    if(contains_invalid_ascii(table_name)):
        return ["Invalid name: '"+table_name.upper()+"'."]
    for func in funcs:
        desc = func(table_name)
        if(desc!="NA"):
            descs.append("Table "+table_name.upper()+" | "+desc + " | " + url)
        if(func == funcs[-1] and len(descs)==0):
            descs.append("Table '"+table_name.upper()+"' not found.")
    return descs
def get_description(table_name):
    descs = []
    if(contains_invalid_ascii(table_name)):
        return "Invalid name: '"+table_name.upper()+"'."
    for func in funcs:
        desc = func(table_name)
        if(desc!="NA"):
            #return("Table "+table_name.upper()+" | "+desc + " | " + url)
            return [table_name.upper(),desc,url]
        if(func == funcs[-1] and len(descs)==0):
            return [table_name.upper(),"NA"]
            #return("Table '"+table_name.upper()+"' not found.")


application = Flask(__name__)

application.secret_key = "super secret key"
"""

"""

rds_username = 'luker1123'
rds_password = 'password'
rds_endpoint = 'descdb.cefwszk3tjwe.us-east-1.rds.amazonaws.com'
rds_database = 'descdb'



# Create the SQLAlchemy engine
application.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqldb://{rds_username}:{rds_password}@{rds_endpoint}/{rds_database}"
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(application)

class Desc(db.Model):
    name = db.Column(db.String(100),primary_key=True)
    desc = db.Column(db.String(100), nullable = False)
    url = db.Column(db.String(100), nullable = False)
    def __init__(self,name,desc,url):  
        self.name = name 
        self.url = url 
        self.desc = desc 

   

def in_db(name):
    with application.app_context():
        existing_item = Desc.query.get(name)
        if not existing_item:
            return False
        return True 
def insert_desc(name,desc,url):
    with application.app_context():
        name = name.replace("/","_")
        new_desc = Desc(name=name,desc=desc,url=url)
        db.session.add(new_desc)
        db.session.commit()

def delete_table(name):
    with application.app_context():
        item = Desc.query.filter_by(name=name).first()
        if(item):
            db.session.delete(item)
            db.session.commit()
def excel_to_db_run():
    excel_name="output"
    df = pd.read_excel(excel_name+".xlsx")
    for i, row in df.iterrows():
        name =str(row['Table Name'])
        name = name.replace("/","_")
        if(not in_db(name)):
            url = str(row['URL'])
            desc = str(row['Description'])
            insert_desc(name,desc,url)
        



@application.before_request
def before_request():
    if not hasattr(g, 'db'):
        g.db = db
@application.route('/', methods=['GET', 'POST'])
def index():
    search = DescriptionSearch(request.form)
    if request.method == 'POST':
        if request.form.get('Action') == 'Search':
            return search_results(search)
        if request.form.get('Action') == 'Inventory':
            return redirect('/descriptions')
        if request.form.get('Action') == 'Home':
            return redirect('/')
    return render_template('index.html', form=search)

@application.route('/results')
def search_results(search):
    
    search_string = search.data['search']
    search_select = search.data['select']
    if search_string:
        if search_select == 'All Sources':
            descs = get_descriptions(search_string)
            for desc in descs:
                flash(desc)
        else:
            if(not in_db(search_string)):
                print("start")
                descs = get_description(search_string)
                print("end")
                if(descs[1]=="NA"):
                     flash("Table '"+descs[0].upper()+"' not found.")
                else:
                    insert_desc(descs[0].upper(),descs[1],descs[2])
                    flash("Table "+descs[0].upper()+" | "+descs[1] + " | " + descs[2])
            else:
                table = Desc.query.get(search_string) 
                flash("Table "+table.name+" | "+table.desc + " | " + table.url)
                
        return redirect('/')
    else:
        flash('No Table entered.')
        return redirect('/')
    
@application.route('/descriptions',methods=['GET', 'POST'])
def descriptions():
    if request.method == 'POST':
        if request.form.get('Action') == 'Home':
            return redirect('/')
        
    with application.app_context():
        data =Desc.query.all()
       
    #return render_template("descriptions.html", data=data)   
    return render_template("test.html", data=data)
@application.route('/delete/<id>/', methods = ['GET', 'POST'])
def delete(id):
    delete_table(id)
    flash("Book is deleted")
    return redirect(url_for('descriptions'))
@application.route('/update/', methods = ['POST'])
def update():
    if request.method == "POST":
        name = request.form.get('Name')
        
        my_data = Desc.query.get(str(name))
        
        my_data.name = request.form['Name']
        my_data.desc = request.form['Description']
        my_data.url = request.form['theurl']
        db.session.commit()
        flash("Table is updated")
        return redirect(url_for('descriptions'))
@application.route('/add/', methods =['POST'])
def insert_desc2():
    if request.method == "POST":

        name = request.form.get('Name')
        desc = request.form.get('Description')
        URL = request.form.get('URL')
        if(not in_db(str(name))):
            insert_desc(str(name),str(desc),str(URL))
            flash("Table added successfully")
        flash("Table already in database")
        return redirect(url_for('descriptions'))

if __name__ == '__main__':
    application.run()