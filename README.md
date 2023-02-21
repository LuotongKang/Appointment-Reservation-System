# Python Application for Vaccine Scheduler
*Objectives: database application development; use SQL from within Python via pymssql.*
This is a vaccine scheduling application (with a database hosted on Microsoft Azure) that can be deployed by hospitals or clinics and supports interaction with users through the terminal/command-line interface. In the real world it is unlikely that users would be using the command line terminal instead of a GUI, but all of the application logic would remain the same. For simplicity of programming, we use the command line terminal as our user interface

## Introduction
A common type of application that connects to a database is a reservation system, where users schedule time slots for some centralized resource. In this assignment you will program part of an appointment scheduler for vaccinations, where the users are patients and caregivers keeping track of vaccine stock and appointments.

This application will run on the command line terminal, and connect to a database server you create with your Microsoft Azure account.

Using the E/R diagram and create table statements in `resources` folder, you will be able to interact with the database using this application. Caregiver and Patient can schedule their vaccine appointments and manage the inventory based on their roles.

## Setup
### Clone the starter code
* scheduler/Scheduler.py:
   * This is the main entry point to the command-line interface application.
   * Once you compile and run Scheduler.py, you should be able to interact with the application.
* scheduler/db/:
   * This is a folder holding all of the important components related to your database.
   * __ConnectionManager.py__: This is a wrapper class for connecting to the database. Read more in 2.3.4.
* scheduler/model/:
   * This is a folder holding all the class files for your data model.
   * You should implement all classes for your data model (e.g., patients, caregivers) in this folder.
* resources/create.sql: SQL create statements for your tables. You should copy, paste, and run the code (along with all other create table statements) in your Azure Query Editor.

### Configure your database connection
#### Installing dependencies and anaconda
Our application relies on a few dependencies and external packages. You’ll need to install those dependencies to complete this assignment.

We will be using Python SQL Driver `pymssql` to allow our Python application to connect to an Azure database. We recommend using Anaconda.

Mac users, follow the instructions in the link to install Anaconda on macOS: https://docs.anaconda.com/anaconda/install/mac-os/
  
Windows users, follow the instructions in the link to install Anaconda on Windows: https://docs.anaconda.com/anaconda/install/windows/. You can choose to install Pycharm for Anaconda, but we recommend installing Anaconda without PyCharm as we will be using the terminal.

After installing Anaconda:
1. We first need to create a development environment in conda.
  * macOS users: launch terminal and navigate to your source directory.
  * Windows users: launch “Anaconda Prompt” and navigate to your source directory.
2. Run `conda create -n [environment name]` to create an environment. Make sure you remember the name of your environment.
3. Activate your environment by running `conda activate [environment name]`. To deactivate, run: `conda deactivate`
4. Run `conda install pymssql` to install the dependencies.

#### Setting up credentials
The first step is to retrieve the information to connect to your Microsoft Azure Database.
* The Server and DB names can be found in the Azure portal.
* The server name would be “data514server.database.windows.net” and the database name would be “data514db”.

__YOU NEED TO CHANGE THIS ACCORDING TO YOUR DATABASE!__
* The User ID would be of the format _<user id>@<server name>_
For example, it could be exampleUser@data514server where “exampleUser” is the login ID which you used to log in to query editor on Azure and “data514server” is the server name.
* Password is what you used to log in to your query editor on the Azure portal.

Once you’ve retrieved the credentials needed, you can set up your environment variables.

#### Setting up environment variables
Make sure to set this in the correct environment if you’re using virtual environments!

In your terminal or Anaconda Prompt, type the following:
```
conda env config vars set Server={}
conda env config vars set DBName={} 
conda env config vars set UserID={} 
conda env config vars set Password={}
```
Where “{}” is replaced by the respective information you retrieved from step 1.
  
You will need to reactivate your environment after that with the command “conda activate [environment name]”

### Verify your setup
Once you’re done with everything, try to run the program and you should see the following output. You should be running the program in terminal (macOS) or Anaconda Prompt (Windows) and in your conda environment.

Note: Command to run the program: “python Scheduler.py” or “python3 Scheduler.py”.
```
Welcome to the COVID-19 Vaccine Reservation Scheduling Application!
*** Please enter one of the following commands ***
> create_patient <username> <password>
> create_caregiver <username> <password>
> login_patient <username> <password>
> login_caregiver <username> <password>
> search_caregiver_schedule <date>
> reserve <date> <vaccine>
> upload_availability <date>
> cancel <appointment_id>
> add_doses <vaccine> <number>
> show_appointments
> logout
> quit
```

If you can see the list of options above, congratulations! You have verified your local setup.

Next, to verify that you have setup your database connection correctly, try to create a caregiver with the command `create_caregiver <username> <password>`. Make sure you have created the tables on Azure before testing this command.

## Codes clarification
### Connection manager
In scheduler.db.ConnectionManager.py, a wrapper class is defined to instantiate the connection to your SQL Server database. Here’s an example of using ConnectionManager.
  
The application is built with a basic use of this connection between database and users' commands.
```
 # instantiating a connection manager class and cursor
cm = ConnectionManager()
conn = cm.create_connection()
cursor = conn.cursor()
```

Here are some examples:
```
# example 1: getting all names and available doses in the vaccine table

  get_all_vaccines = "SELECT Name, Doses FROM vaccines"
try:
    cursor.execute(get_all_vaccines)
    for row in cursor:
        print(name:" + str(row[‘Name’]) + ", available_doses: " + str(row[‘Doses’]))
except pymssql.Error:
    print(“Error occurred when getting details from Vaccines”)

# example 2: getting all records where the name matches “Pfizer”
get_pfizer = "SELECT * FROM vaccine WHERE name = %s"
try:
    cursor.execute(get_pfizer)
    for row in cursor:
        print(name:" + str(row[‘Name’]) + ", available_doses: " + str(row[‘Doses’]))
except pymssql.Error:
    print(“Error occurred when getting pfizer from Vaccines”)
```
Helpful resources on writing pymssql:
   
Documentation -> https://pythonhosted.org/pymssql/ref/pymssql.html
   
Examples -> https://pythonhosted.org/pymssql/pymssql_examples.html

### Entity sets
* Patients: these are customers that want to receive the vaccine.
* Caregivers: these are employees of the health organization administering the vaccines.
* Vaccines: these are vaccine doses in the health organization’s inventory of medical supplies that are on hand and ready to be given to the patients. 

### Error handling
* If the user types a command that doesn’t exist, it is bad to immediately terminate the program. A better design would be to give the user some feedback and allow them to re-type the command. While not all possible inputs are considered, error handling for common errors (e.g., missing information, wrong spelling) is included.
* After executing a command, it should re-route the program to display the list of commands again. For example: If a patient 'reserves' their vaccine for a date, the database wil be updated to reflect this information and the patient will be routed back to the menu again.

### Passwords
Instead of directly storing all password in the database, we've used a technique called salting and hashing. In cryptography, salting hashes refer to adding random data to the input of a hash function to guarantee a unique output. We will store the salted password hash and the salt itself to avoid storing passwords in plain text. Use the following code snippet as a template for computing the hash given a password string:
```
import hashlib
import os
# Generate a random cryptographic salt
salt = os.urandom(16)
# Generate the hash
hash = hashlib.pbkdf2_hmac(
   'sha256',
   password.encode('utf-8'),
   salt,
   100000,
   dklen=16
)
```

## Functionalities
The following operations were implemented:
* `create_patient <username> <password>` & `create_caregiver <username> <password>`
  * Print `Created user {username}` if create was successful.
  * If the user name is already taken, print `Username taken, try again!`.
  * For all other errors, print `Failed to create user.`.
* `login_patient <username> <password>` & `login_caregiver <username> <password>`
  * If a user is already logged in in the current session, print `User already logged in.`.
  * For all other errors, print `Login failed.`. Otherwise, print `Logged in as: [username]`.
* `search_caregiver_schedule <date>`
  * Both patients and caregivers can perform this operation.
  * Output the username for the caregivers that are available for the date, along with the number of available doses left for each vaccine. Order by the username of the caregiver. Separate each attribute with a space.
  * If no user is logged in, print `Please login first!`.
  * For all other errors, print `Please try again!`.
* `reserve <date> <vaccine>`
  * Patients perform this operation to reserve an appointment.
  * Caregivers can only see a maximum of one patient per day, meaning that if the reservation went through, the caregiver is no longer available for that date.
  * If there are available caregivers, choose the caregiver by alphabetical order and print `Appointment ID: {appointment_id}, Caregiver username: {username}`.
  * Output the assigned caregiver and the appointment ID for the reservation.
  * If there’s no available caregiver, print `No Caregiver is available!`. If not enough vaccine doses are available, print `Not enough available doses!`.
  * If no user is logged in, print `Please login first!`. If the current user logged in is not a patient, print `Please login as a patient!`.
  * For all other errors, print `Please try again!`.
* `add_doses <vaccine> <number>`
  * Vaccines inventory increase, which will be reflected in the database.
* `show_appointments`
  * Output the scheduled appointments for the current user (both patients and caregivers).
  * For caregivers, it should print the appointment ID, vaccine name, date, and patient name. Order by the appointment ID. Separate each attribute with a space.
  * For patients, it should print the appointment ID, vaccine name, date, and caregiver name. Order by the appointment ID. Separate each attribute with a space.
  * If no user is logged in, print `Please login first!`.
  * For all other errors, print `Please try again!`. 
* `Logout`
  * If not logged in, it should print `Please login first.`. Otherwise, print `Successfully logged out!`.
  * For all other errors, print `Please try again!`.

For most of the operations mentioned below, The program will do some checks to ensure that the appointment can be reserved (e.g., whether the vaccine still has available doses).
         
## Extra funcionalities
1. Only strong passwords are allowed:
  * At least 8 characters.
  * A mixture of both uppercase and lowercase letters.
  * A mixture of letters and numbers.
  * Inclusion of at least one special character, from “!”, “@”, “#”, “?”.
2. Both caregivers and patients can cancel an existing appointment.
