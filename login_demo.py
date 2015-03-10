# run -- sqlite3 onedir.db < ondir_create_table -- in shell

import sqlite3 as lite
import sys

def print_version_demo():
    con = None

    try:
        # connect() returns a connection object
        con = lite.connect('onedir.db')
        # cursor() returns a cursor object
        # cursor is used to traverse the records from the result set
        cur = con.cursor()
        cur.execute('SELECT SQLITE_VERSION()')
        # fetchone gets the next row of the query result set
        data = cur.fetchone()
        # print data
        print "SQLite version: %s" % data

    except lite.Error, e:

        print "Error %s:" % e.args[0]
        sys.exit(1)

    finally:
        # closes connection to database
        if con:
            con.close()

def register_user(u,p,r):
    returnValue = ' '
    try:    
	u = str(u)
	p = str(p)
	r = str(r)
    except UnicodeError:
	returnValue = "input is invalid";
	

    con = lite.connect('onedir.db')

    with con:
	
	con.row_factory = lite.Row
        cur = con.cursor()

        #cur.execute("DROP TABLE IF EXISTS onedir_login")
        cur.execute("CREATE TABLE IF NOT EXISTS onedir_login(username TEXT, password TEXT, role TEXT)")

	sql_cmd =  "SELECT * FROM onedir_login"
        cur.execute(sql_cmd)
        rows = cur.fetchall()

        does_not_exist_flag = True
        for row in rows:
            username = (row["username"] + ' ').strip()
            if row is None: 
                break
            if (username == u):
                does_not_exist_flag = False
                break
	# if the username does not exists
        if does_not_exist_flag == True:
            returnValue = "user %s has been created" % u
            sql_cmd = "INSERT INTO onedir_login VALUES(?, ?, ?)"
            cur.execute(sql_cmd, (u, p, r))
	else:
	    returnValue = "user %s already exists" % u	    
 
    return returnValue

def retrieve_login_info():
    user_passwd_dict = {}
    con = lite.connect("onedir.db")
    with con:
        # select a dictionary cursor
        # this allows you to access records by names of columns
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM onedir_login")
        rows = cur.fetchall()

        for row in rows:
	    username = str(row["username"])
	    password = str(row["password"])
	    role = str(row["role"])
	    user_passwd_dict[username] = (password, role)
            #print "%s %s" % (row["username"], row["password"])
    return user_passwd_dict

def delete_user(u):
    con = lite.connect("onedir.db")
    try:    
	u = str(u)
    except UnicodeError:
	returnValue = "input is invalid";

    with con:
        # select a dictionary cursor
        # this allows you to access records by names of columns
        con.row_factory = lite.Row
        cur = con.cursor()
	query = "DELETE FROM onedir_login WHERE username='%s'" % u
        cur.execute(query)
    return
 
def change_password(u,p):
    returnValue = ' '
    try:    
	u = str(u)
	p = str(p)
    except UnicodeError:
	returnValue = "input is invalid";
	
    con = lite.connect('onedir.db')
    with con:
	con.row_factory = lite.Row
        cur = con.cursor()
	sql_cmd =  "UPDATE onedir_login SET password='%s' WHERE username='%s'" % (p,u)
        cur.execute(sql_cmd)  

    return 




def login(u,p):
    returnMessage = ' '
    userRole = ' '
    u = (u + ' ').strip()
    p = (p + ' ').strip()
   # u = u[:-1]

    con = lite.connect("onedir.db")
    with con:
        # select a dictionary cursor
        # this allows you to access records by names of columns
        con.row_factory = lite.Row
        cur = con.cursor()


        sql_cmd =  "SELECT * FROM onedir_login"
        cur.execute(sql_cmd)
        rows = cur.fetchall()
        flag = False
        for row in rows:
            username = (row["username"] + ' ').strip()
            if row is None:
                returnValue = "username not found"
                flag = True
	        returnRole = "none"
                break
            if (username == u and row["password"] == p):
                returnValue = "Logged In"
                flag = True
		print row["role"]	    
                userRole = str(row["role"])
                break
            if (username == u and row["password"] != p):
                returnValue = "invalid password"
	        userRole = "none"
                flag = True
                break
        if flag == False:
            returnValue = "username not found"
	    returnRole = "none"

    return (returnValue, userRole)

def main():
    print register_user("ROOT", "1", "admin")
    print register_user("a", "2", "user")
    print register_user("b", "3", "user")
    print retrieve_login_info()
    print login("ROOT", "1")
    change_password("b", "9")
    print retrieve_login_info()


if __name__ == '__main__':
    main()
