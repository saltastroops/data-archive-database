# SALT/SAAO Data Archive Database

## Introduction

The SALT/SAAO Data Archive is used for storing and managing the observation data produced with the Southern African 
Large Telescope (SALT) and other telescopes in Sutherland (South Africa). 
The stored data is made accessible to the public. The users may search and request data to download for personal use.

The SALT/SAAO Data Archive Database is used to store all the data regarding the SALT/SAAO Data Archive.
This repository explains in details how get started and actually store the data in the SALT/SAAO Data Archive Database.

## Setting up

[Python3](https://www.python.org/downloads/), [Pip](https://pypi.org/project/pip/) which comes bundled by default with 
Python 3, [Git](https://git-scm.com/), [python virtual environment](https://virtualenv.pypa.io/en/stable/), and [MySQL](https://www.mysql.com/) must be installed on your machine.

Clone this repository to a location of your choice.

```commandline
git clone git@github.com:saltastroops/data-archive-database.git
```

Then navigate to the root directory.

```commandline
cd data-archive-database
```
Install the python virtual environment. For Ubuntu OS, execute the following command

```bash
sudo apt-get install python3-venv
```

In the data-archive-database directory, create the [python virtual environment](https://virtualenv.pypa.io/en/stable/), 
which is a complete copy of the Python interpreter.

```commandline
python3 -m venv venv
```

With this command, python will execute the venv package which create a virtual environment named venv.

After the virtual environment is created, it must be activated by executing the following command.

```commandline
source venv/bin/activate
```

Now, a virtual environment should be activated, to confirm it is, the output will look like below

```
(venv)/path/to/this/directory
```

Now, since Python 3 (assuming it is installed) comes bundled with Pip, so we can use pip command straight away to 
install are the required packages. All the packages are in the `requirements.txt` file

```commandline
pip install -r requirements.txt
```

There are multiple databases connected to for data retrieval and data storage. Depending whether it is SALT or SAAO,
there required environment variables for establishing the connection to those databases.

e.g For SALT, the following environment variables ar required.

### SALT/SAAO Data Archive Database

Variable | Description | Example
---- | ---- | ----
SSDA_USER | The SALT/SAAO Data Archive database user | username
SSDA_HOST | The SALT/SAAO Data Archive database host server | username@ssdadb.saao.ac.za
SSDA_DATABASE | The SALT/SAAO Data Archive database name | database
SSDA_PASSWORD | The SALT/SAAO Data Archive database password | databasepassword


### SALT Database

Variable | Description | Example
---- | ---- | ----
SDB_USER | The SALT database user | username
SDB_HOST | The SALT database host server | username@sdb.saao.ac.za
SDB_DATABASE | The SALT database name | database
SDB_PASSWORD | The SALT database password | databasepassword


### Data File BasePath

Variable | Description | Example
---- | ---- | ----
DATA_FILE_BASE_PATH | The path to where the fits files are located | /base/path/to/data


When all that is set, should be good to run the SQL script for creating the data archive database with it tables.
Assuming that mysql is installed, execute the following commands.

###### Enter the mysql execution point

```commandline
mysql -u "salt/sooa data archive database username" -p
```

You will be prompted to enter a password, do so.

###### Choose database to use

```mysql
use "salt/saao database name";
```

###### Execute the sql script

```commandline
source ./sql/tables.sql
```

If all went well, a SALT/SAAO Data Archive database should be created with it tables.

Now, we can run the python script for populating the SAL/SAAO Data Archive database.

```commandline
python3 run.py
```

The tables in the database should be populated.



