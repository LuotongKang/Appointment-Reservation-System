from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]

    # check 2: check if the username has been taken already
    if username_exists(username, "Patients"):
        print("Username taken, try again!")
        return

    # extra credit
    early_return = False
    special = any(not c.isalnum() for c in str(password))
    upper = any(c.isupper() for c in str(password))
    lower = any(c.islower() for c in str(password))

    if len(password) < 8:
        print("The passwords should be at least 8 characters")
        early_return = True
    if not special:
        print("Please include at least 1 special character in your passwords")
        early_return = True
    if not upper:
        print("Please include at least 1 uppercase letter in your passwords")
        early_return = True
    if not lower:
        print("Please include at least 1 lowercase letter in your passwords")
        early_return = True
    if early_return:
        return


    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists(username, "Caregivers"):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists(username, role="Caregivers"):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM " + role + " WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return
    if len(tokens) != 3:
        print("Login failed")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return
    if len(tokens) != 3:
        print("Login failed")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # search_caregiver_schedule <date>
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if len(tokens) != 2:
        print("Please try again.")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    date_tokens = tokens[1].split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    caregiver_schedule = "(SELECT DISTINCT A.username FROM Availabilities AS A WHERE A.time = %s)" +\
        " EXCEPT (SELECT B.cname FROM Appointments AS B WHERE B.time = %s) ORDER BY A.username"
    doses_available = "SELECT V.name, (SELECT V1.doses FROM Vaccines AS V1 WHERE V1.name=V.name)" +\
        "-(SELECT COUNT(*) FROM Appointments AS A WHERE A.vname=V.name) FROM Vaccines AS V"
    try:
        d = datetime.datetime(year, month, day)
        cursor.execute(caregiver_schedule, (d, d))
        text1 = cursor.fetchall() # [(user1,), (user2,)]
        cursor.execute(doses_available)
        text2 = cursor.fetchall() #[('moderna', 2), ('pfizer', 5)]
        if len(text1) > 0:
            print("Available caregivers:")
            for row in text1:
                print(row[0])
        else:
            print("No Caregiver is available!")
        if len(text2) > 0:
            sum_dose = 0
            for vac in text2:
                sum_dose += vac[1]
            if sum_dose == 0:
                print("Not enough available doses:")
            else:
                print("Available doses:")
        for row in text2:
                print(row[0] + " " + str(row[1]))
        else:
            print("No vaccines inventory!")

    except pymssql.Error as e:
        # print("Please try again!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def reserve(tokens):
    # reserve <date> <vaccine>
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if current_patient is None:
        print("Please login as a patient!")
        return
    if len(tokens) != 3:
        print("Please try again.")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    date_tokens = tokens[1].split("-")
    if len(date_tokens) != 3:
        print("Please try again.")
        return
    else:
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        vaccine = tokens[2]

    caregiver_schedule = "(SELECT DISTINCT A.username FROM Availabilities AS A WHERE A.time = %s)" +\
        " EXCEPT (SELECT B.cname FROM Appointments AS B WHERE B.time = %s) ORDER BY A.username"
    doses_available = "SELECT V.name, (SELECT V1.doses FROM Vaccines AS V1 WHERE V1.name=V.name)" +\
        "-(SELECT COUNT(*) FROM Appointments AS A WHERE A.vname=V.name) FROM Vaccines AS V"
    add_appointment = "INSERT INTO Appointments VALUES (%d, %s, %s, %s, %s)"

    try:
        d = datetime.datetime(year, month, day)
        cursor.execute(caregiver_schedule, (d, d))
        temp = cursor.fetchall() # [(user1,), (user2,)]
        # check schedule
        return_early = False
        if len(temp) == 0:
            print("No Caregiver is available!")
            return_early = True
        else:
            caregiver_available = list(map(list, zip(*temp)))[0]
        # generate unique appointment_id -- consider use AUTOINCREMENT
        cursor.execute("SELECT COUNT(*) FROM Appointments")
        if cursor.fetchall()[0][0] == 0:
            appt_id = 1
        else:
            cursor.execute("SELECT MAX(id) FROM Appointments")
            appt_id = cursor.fetchall()[0][0] + 1
        # check inventory
        cursor.execute(doses_available)
        vac_remained = dict(cursor.fetchall()) # {'moderna': 2, 'pfizer': 5}
        if (vaccine not in vac_remained) or (vac_remained[vaccine] == 0):
            print("Not enough available doses!")
            return_early = True
        if return_early:
            return
        # Update datebase
        cursor.execute(add_appointment, (appt_id, caregiver_available[0], d, current_patient.get_username(), vaccine))
        conn.commit()
        print("Appointment ID: " + str(appt_id) + ", Caregiver username: " + str(caregiver_available[0]))
    except pymssql.Error as e:
        # print("Please try again!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def upload_availability(tokens):
    #  upload_availability <date>
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return
    if len(tokens) != 2:
        print("Please try again.")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        # uploading repeated availability will cause this error
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    # cancel <appointment_id>
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if len(tokens) != 2:
        print("Please try again.")
        return
    appt_id = tokens[1]
    if current_caregiver is None:
        query_for_name = "SELECT pname FROM Appointments WHERE id = %s"
        name = current_patient.get_username()
    else:
        query_for_name = "SELECT cname FROM Appointments WHERE id = %s"
        name = current_caregiver.get_username()
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query_for_name, appt_id)
        tuple_appt =  cursor.fetchall()
        if len(tuple_appt) == 0:
            print("Cannot find appointment")
            return
        if tuple_appt[0][0] != name:
            print("It's not your appointment. Please try again!")
            return
        cursor.execute("DELETE FROM Appointments WHERE id = %s", appt_id)
        conn.commit()
        print("Appointment canceled")
    except pymssql.Error as e:
        # print("Please try again!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return
    if len(tokens) != 3:
        print("Please try again.")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if len(tokens) != 1:
        print("Please try again.")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    caregiver_appt = "SELECT A.id, A.vname, A.Time, A.pname FROM Appointments as A WHERE A.cname = %s ORDER BY A.id"
    patient_appt = "SELECT A.id, A.vname, A.Time, A.cname FROM Appointments as A WHERE A.pname = %s ORDER BY A.id"

    try:
        if current_caregiver is not None:
            name = current_caregiver.get_username()
            cursor.execute(caregiver_appt, name)
            appointments_ls = cursor.fetchall()
            print_line = "Hello Caregiver " + name
        else:
            name = current_patient.get_username()
            cursor.execute(patient_appt, name)
            appointments_ls = cursor.fetchall()
            print_line = "Hello Patient " + name
        if len(appointments_ls) == 0:
            print_line += ", you don't have any appointments."
        else:
            print_line += ", you've made appointments below:"
        print(print_line)
        for row in appointments_ls:
            print(str(row[0]) + " " + row[1] + " " + str(row[2]) + " " + row[3])

    except pymssql.Error as e:
        # print("Please try again!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def logout(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if len(tokens) != 1:
        print("Please try again.")
        return
    current_caregiver = None
    current_patient = None
    print("Successfully logged out!")
    return


def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break
        tokens = response.split(" ")
        operation = tokens[0]
        if (operation == "create_patient") or (operation == "create_caregiver"):
            position = 0
            response = ""
            for token in tokens:
                if position == 2:
                    response += token + " "
                else:
                    response += token.lower() + " "
                position += 1
        else:
            response = response.lower()
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == 'cancel':
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")

if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()