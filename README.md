# Populating the SAAO/SALT Data Archive Database

This application lets you populate (and update) the SAAO/SALT Data Archive database.

## Installation and configuration

Ensure that Python 3.7 is running on your machine. You can check this with the `--version` flag.

```bash
python3 --version
```

Then clone the package from its repository,

```bash
git clone https://github.com/saltastroops/data-archive-database.git
```

and make sure you are in the master branch,

```bash
git checkout master
```

Then create a virtual environment to manage python packages using the [venv module](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

```bash
python3 -m venv venv
```

**NB!** the first ```venv``` is the python3 module whereas the second ```venv``` is the directory 
where the virtual environment files reside.

To activate the virtual environment run the command below,

```bash
source venv/bin/activate
```

Then install the packages from the requirements.txt file,

```bash
pip install -r requirements.txt
```

Before using the package you need to define the following environment variables.

Variable name | Explanation | Example
--- | --- | ---
SSDA_DSN | Data source name of the data archive database | postgresql://ssda:secret@example.host.za:port/ssda
SDB_DSN | Data source name of the SALT science database | mysql://salt:secret@example.host.za:port/sdb

See below for instructions on how to run the script as a cron job.

## Setting up the database

Flyway is used for initialising and updating the database, so this needs to be installed first.

### Installing Flyway on Ubuntu

Follow the [installation instructions](https://flywaydb.org/documentation/commandline/#download-and-installation).

### Installing Flyway on macOS

You can follow the [installation instructions](https://flywaydb.org/documentation/commandline/#download-and-installation). However, it might be easier to just use brew:

```bash
brew install flyway 
```

### Installing pgSphere

The data archive database requires [pgSphere](https://pgsphere.github.io/doc/index.html), which provides various spherical data types, functions and operators.

To install it on **MacOS**, first make sure that pg_config is available on the server.

```bash
pg_config --help
```

Then clone the pgSphere source code from [its GitHub repository](https://github.com/akorotkov/pgsphere),

```bash
git clone https://github.com/akorotkov/pgsphere
```

and change into the created directory,

```bash
cd pgsphere
```

Then execute

```bash
make USE_PGXS=1 PG_CONFIG=`which pg_config`
```

followed by

```bash
sudo make USE_PGXS=1 PG_CONFIG=`which pg_config` install
```

To install it on **Ubuntu**.

Run update command to update package repositories and get latest package information.
```bash
sudo apt-get update -y
```

Run the install command with -y flag to quickly install the packages and dependencies.
```bash
sudo apt-get install -y postgresql-10-pgsphere
```

### Creating and initialising the database

Login to the PostgreSQL server and create the database,

```postgresql
CREATE DATABASE ssda;
```

and exit PostgreSQL again.

Make sure you are in the root directory of the project and run Flyway:

```bash
flyway -url=jdbc:postgresql://your.host:5432/ssda -user=admin -locations=filesystem:sql migrate
```

This assumes that the PostgreSQL server is listening on port 5432 and that there is a user `admin` with all the necessary permissions.

Once the database is initialised, there will be the following new roles:

Role | Description
--- | ---
admin_editor | May insert, update and delete admin data.
observations_editor | May insert, update and delete observation data.

The permissions are limited to those necessary for the relevant tasks. For example, the observations_editor may only delete some of the observation data.

While roles are created, users aren't. So for example, if you want to have a dedicated user for populating the observations database, you may run a SQL commands like the following.

```postgresql
CREATE ROLE obs PASSWORD 'secret' LOGIN INHERIT;
GRANT observations_editor TO obs;
```

## Updating

### Updating the script

In order to update the script, make sure you are in the master branch

```bash
git checkout master
```

and pull the changes from the remote repository,

```bash
git pull
```

Finally update the installed package.

```bash
pip install -e .
```

### Updating the database

To update the database you execute Flyway the same way as for initialising it:

```bash
flyway -url=jdbc:postgresql://your.host:5432/ssda -user=admin -locations=filesystem:sql -schemas=public,admin,observations,extensions migrate
```

## Usage

The package provides a command `ssda` for inserting, updating and deleting entries in the Data Archive database.

To find out about the available options you may use the `--help` option.

```bash
ssda --help
``` 

The various tasks for modifying the database are explained in the following sections.

The default behaviour of the command is to terminate if there is an error. However, if the `--skip-errors` flag is included, the command will instead proceed with inserting the next FITS file.

### Inserting observations

The `insert` task allows you to create new database entries from FITS files. Typically you use it to create entries for a range of dates.

```bash
ssda --task insert --mode production --fits-base-dir /path/to/fits/files --start 2019-06-25 --end 2019-06-27
```

Both start and end date must be given, and they must be of the format `yyyy-mm-dd`. The start date is inclusive, the end date inclusive. Both refer to the beginning of the night. So in the above example FITS files would be considered for the time between noon of 25 June and noon of 27 June 2019.

For convenience, you may use the keyword 'yesterday', which will be replaced with (gasp!) yesterday's date. Another choice is the keyword `today`, which means, well, today's date. So if you want to insert last night's data, you can run

```bash
ssda --task insert --mode production --fits-base-dir /path/to/fits/files --start yesterday --end today
```

Existing database content is not changed when inserting. This implies that it is safe to re-run the command as often as you like.

By default FITS files for all instruments are considered. However, you can limit insertions to a single instrument by adding the `--instrument` option.

```bash
ssda --task insert --mode production --fits-base-dir /path/to/fits/files --start yesterday --end today --instrument RSS
```

The spelling of the instrument name is case-insensitive. Hence you might also have run the command as

```bash
ssda --task insert --mode production --fits-base-dir /path/to/fits/files --start yesterday --end today --instrument rss
```

You can limit insertion to a set of instruments by using the `--instrument` option more than once.

```bash
ssda --task insert --mode production --fits-base-dir /path/to/fits/files --start yesterday --end today --instrument RSS --instrument Salticam
```

### Updating observation data

[TBD]

### Deleting observations

You can use the `delete` task to delete database entries and their corresponding preview files. The usage is the same as for the `insert` task. For example, the following command will delete all observation entries for the night starting on 8 June 2019.

```bash
ssda --task delete --mode production --fits-base-dir /Users/christian/Desktop/FITS_FILES --start 2019-06-08 --end 2019-06-09
``` 

Note that no proposal entries are deleted, even if none of their associated observations are left.

### Options

As explained in the previous subsections, the `ssda` command accepts the following options.

Option | Explanation
--- | ---
--end | End date (exclusive) of the date range to consider.
--fits-base-dir | Base directory containing all the FITS files.
--instrument | Instrument whose FITS files shall be considered. This option may be used multiple times unless the `--file` flag is used.
-h / --help | Display a help message.
--start | Start date (inclusive) of the date range to consider.
--skip-errors | Do not terminate if there is an error.

## Logging in verbosity mode

You can choose the degree of verbosity with the `--verbosity` option.

```bash
python cli.py --verbosity 1 insert --start yesterday --end yesterday
```

#### Verbosity options

Verbosity Option | Explanation
--- | ---
0 | Don't output anything.
1 | Output the FITS file path and the error message.
2 | Output the FITS file path and error stacktrace.

## Running the application as a cron job.

In case you plan to run the application as a cron job, you should create the `.bashrc` file in the home directory (if it does not exist yet) and define the required environment variables in that file.

```bash
export FITS_BASE_DIR=/path/to/fits/files
export PREVIEW_BASE_DIR=/path/to/preview/files
# ... export commands for all the other environment variables ...
``` 

Assuming that the application is in the folder `/home/ssda/applications/database-update`, that you want to insert last night's content, update the observation status and proposal investigators before, and that you want to log errors to the file `/home/ssda/logs/database-update.txt`, you should then open the crontab file,

```bash
crontab -e
```

and add code like the following to it.

```text
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
SSDA_LOG=/home/ssda/logs/database-update.txt
8 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose update --start last-year --end yesterday --scope observations > $SSDA_LOG 2>&1
9 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose update --start last-year --end yesterday --scope proposals > $SSDA_LOG 2>&1
10 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose insert --start yesterday --end yesterday > $SSDA_LOG 2>&1
```

## Extending the code

### Using an additional Python library

If you need to make use of a new Python library, you need to install it with `pip`.

```bash
pip install new_package
```

### Accessing a new database

All databases connections should be defined in the file `src/ssda/connection.py`. For example, the code for a new database called IRSF might look as follows.

```python
import os
from pymysql import connect, Connection, cursors

irsf_config = {
    "user": os.environ["IRSF_USER"],
    "host": os.environ["IRSF_HOST"],
    "password": os.getenv("IRSF_PASSWORD"),
    "db": os.getenv("IRSF_DATABASE"),
    "charset": "utf8",
    "cursorclass": cursors.DictCursor,
}

def irsf_connect() -> Connection:
    return connect(**irsf_config)
```

As shown in this example, all the connection parameters should be provided in form of environment variables. In particular, do not hard-code the username and password. Remember to update the table of environment variables in the [installation and configuration section](#installation-and-configuration) above.

### Adding an institution

A new institution must be added to the Institution table in the SSDA database. For example, in order to add the University of Wakanda as an institution, you would have to execute the following SQL statement,

```mysql
INSERT INTO Institution (institutionName) VALUES ('University of Wakanda')
```

Afterwards you have to add the institution as an enum member to the `Institution` enumeration in the file `ssda/institution.py`,

```python
UNIVERSITY_OF_WAKANDA = "University of Wakanda"
```

The enum member (`University of Wakanda` in this case) must be the same as the value of the `institutionName` column in the Institution table.

### Adding a telescope

A new telescope must be added to the Telescope table in the SSDA database, and if it is owned by a new institution this institution needs to be added to the Institution table, as explained above.

For example, assume that the institutionId column of the Institution table has the value 42 for the University of Wakanda. Then in order to define a telescope called Ikhwezi, owned by the University of Wakanda, you would run the following SQL statement,                                              `

```mysql
INSERT INTO Telescope (telescopeName, ownerId) VALUES ('Ikhwezi', 42)
```

Once the database has been updated, you should add the new telescope as an enum member to the `telescope` class in the file `ssda/telescope.py`.

```python
IKHWEZI = "Ikhwezi"
```

Note that the enum member value (`Ikwezi` in this case) must be the same as the value of the telescopeName column in the Telescope table.

If the new telescope makes use of an existing instrument, you have to update the `InstrumentFitsData` implementation for that instrument (see next section).

### Adding or updating an instrument

To add a new instrument, you must add a table for its FITS data to the SSDA database. This table must contain an id column (serving as the primary key), a telescopeId column (with a foreign key to the telescopeId column in the Telescope table) and any other columns.

As an example, assume there is a new instrument called Isibane, and you want to store an exposure time and an articulation angle for it. Then the SQL statement for its table might look like the following.

```mysql
CREATE TABLE Isibane (
    isibaneId INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique id' ,
    telescopeId INT(11) UNSIGNED NOT NULL COMMENT 'Telescope that took the data',
    articulationAngle FLOAT NOT NULL COMMENT 'Articulation angle',
    KEY `fk_TelescopeIsibane_idx` (`telescopeId`),
    CONSTRAINT `fk_TelescopeIsibane` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeid`)
)
```

Once you have created this table, you need to define two files:

* A text file `src/ssda/instrument/isibane_keywords.txt` defining FITS header keywords and corresponding columns in the `Isibane` table just created. The name of the file is arbitrary, but sticking to the standard (lower case instrument name plus `'_keywords.txt') seems like a reasonable idea.

  For our example detector the file content might look as follows.

```text
# RSS header keywords and database columns

# First column is for FITS headers
# Second column is for table field

AR-ANGLE      				articulationAngle
EXPTIME      				exposureTime
```

* A Python file `src/ssda/instrument/isidibane_fits_data.py` defining a class `IsidibaneFitsData` which extends the abstract base class `ssda.instrument.InstrumentFitsData` for the new detector. This class needs to implement all the abstract methods of `InstrumentFitsData`. The name of the file and class are arbitrary, but again sticking to the standard used for the existing ones is a good idea.

  The `instrument_details_file` method returns the file path of the file mapping FITS header keywords and column names created above. Obviously its return value must be consistent with the chgoices youy've made for the file name (and its path).
  
  The `instrument_table` returns the name of the instrument table created above. Unsurprisingly, its return value must be the same as the table name you've chosen.
  
Finally, you need to add an enum member for the new instrument to the enumeration in `src/ssda/instrument.instrument.py` and modify the enumeration's `fits_data_class` method.

```python
from enum import Enum
from typing import Type

from instrument_fits_data import InstrumentFitsData
from ssda.instrument.instrument import HrsFitsData
from ssda.instrument.instrument import UkukhanyaFitsData
from ssda.instrument.instrument import RssFitsData
# ... other imports ...

class Instrument(Enum):
    HRS = "HRS"
    UKUKHANYA = "Ukukhanya"
    RSS = "RSS"
    # ... other enum members ...

    def fits_data_class(self) -> Type[InstrumentFitsData]:
        """
        The type to use for creating FITS data access instances for this instrument.

        Note that a type is returned, so that you still have to call the constructor to
        get an InstrumentFitsData. For example:

        night = datetime.date(2019, 6, 18)

        fits_data_class = Instrument.RSS.fits_data_class()
        fits_data = fits_data_class(night)
        print(fits_data.fits_files())

        Returns
        -------
        fits_data_type : type
            InstrumentFitsData type.

        """
        if self == Instrument.HRS:
            return HrsFitsData
        elif self == Instrument.ISIBANE:
            return UkukhanyaFitsData
        elif self == Instrument.RSS:
            return RssFitsData
        # ... elif clauses for other enum members ...
        else:
            raise ValueError('No InstrumentFitsData type found for {}'.format(self.value))
```

With these changes in place you can populate the database from the new instrument's FITS files, as you can for the previously existing instruments.

In order to update an instrument you just have to change the database tables and the above files as required.

# Adding https using a self-signed certificate to the SALT/SAAO Data Archive

Before you begin, you should have a non root user with sudo privileges.

We also need  to have Nginx installed. To check if Nginx is installed and running, you run the following command:
```bash
  service nginx status
```
If Nginx is not installed in your system, you can follow this guide [installing Nginx](https://www.nginx.com/resources/wiki/start/topics/tutorials/install/) 

We can create a self-signed key and certificate pair using the following command
``` bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt
```
You will be asked a series of questions about our server in order to add the required information correctly in our certificate

The prompts will look something like this

```text
Country Name (2 letter code) []:
State or Province Name (full name) []:
Locality Name (example: city) []:
Organization name (e.g company) []:
Organization Unit Name (eg, section) []:
Common Name (e.g server FQDN or YOUR name) []:
Email Address []:
```
You will need to answer these prompts appropriately. Two files will then be created in the appropriate
subdirectories of the  ```/etc/ssl``` directory.

We then need to create a strong Diffie-Helman group which is used in negotiating Perfect Forward Secrecy with clients.
We can do this by running the code below:

```bash
sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
``` 

## Configuring Nginx to use SSL

In order to do this we need to create a configuration snippet pointing the SSL key and Certificate
To distinguish the file from the rest we can call it `your-file-name`.conf

```bash
sudo nano /etc/nginx/snippets/your-filename.conf
```
You can replace `your-filename` with any file name you choose. Inside the file we just created we need
to set the `ssl_certificate` directive to our certificate file and the `ssl_certificate_key` to the associated key.

```text
 ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
 ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key; 
```
The snippet above must be in  file. Save and close the file when done.

## Creating a configuration snippet with strong encryption settings
___
We now need another code snippet to define some SSL settings so we can keep our server secure. We have to create a new 
file in the location /etc/nginx/snippets

```bash
 sudo nano /etc/nginx/snippets/ssl-params.conf
``` 

Copy the following snippet into your `ssl-params.conf` snippet file:

```text
ssl_protocols TLSv1.2;
ssl_prefer_server_ciphers on;
ssl_dhparam /etc/nginx/dhparam.pem;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
ssl_ecdh_curve secp384r1; # Requires nginx >= 1.1.0
ssl_session_timeout  10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off; # Requires nginx >= 1.5.9
ssl_stapling on; # Requires nginx >= 1.3.7
ssl_stapling_verify on; # Requires nginx => 1.3.7
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
# Disable strict transport security for now. You can uncomment the following
# line if you understand the implications.
# add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
```
Since we are using a self-signed certificate, the SSL-stapling will not be used and because of this, Nginx
will give a warning, disable stapilng for our self-signed certificate and then continue
working as it should. 

We then need to adjust the Nginx configuration to use SSL

This setup assumes you are having  a custom server block configuration file in `/etc/nginx/sites-available` directory. 
Before changing your Nginx configuration file, you must do a backup for it in case of problems arsing in your file:

```bash
sudo cp /etc/nginx/sites-available/filename /etc/nginx/sites-available/filename.bak
``` 
Replace `filename` with the name of your Nginx configuration file. Now open the configuration file and make these
adjustments.

```bash
 sudo nano /etc/nginx/sites-available/filename
``` 
Your configuration file might look something like this:

```text
server {
    listen 80;
    listen [::]:80;

    server_name your-servername;
}
```
We now need to add the following snippet in the server block underneath `server_name`
```text
    return 302 https://$server_name$request_uri;
```
This snippet above allows us to redirect to HTTPS.  

Inside your file, create a new server block, add the following:

```text
server{
     listen 443 ssl;
     listen [::] 443 ssl;
     include snippets/your-filename.conf;
     include snippets/ssl-params.conf; 
    
     server_name your-servername;
}   
```
Replace `your-filename` with the file name of the `.conf` file we created earlier and `your-servername` with name of 
your server, the save and close the file.

We now focus on the firewall. If you have ufw firewall enabled, you will need to adjust the settings to allow for SSL 
traffic. We can see the available ufw profiles added by Nginx upon installation by typing:

```bash
sudo ufw app list
```  

We can also see the current setting by typing:

```bash
 sudo ufw status
```
This will show that only HTTP traffic is allowed in the web server, so to change this we need to allow the `Nginx Full`
profile and then delete the redundant Nginx HTTP profile allowance by typing the following:
 ```bash
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 'Nginx HTTP'
```
Now we need to restart Nginx to implement the changes we have made. We need to first check that we don't have any syntax
errors in our files by running the following command:

```bash
sudo nginx -t
``` 

If it passes, this means everything was successful and you will get a result which may look like the following:

```text
nginx: [warn] "ssl_stapling" ignored, issuer certificate not found
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

The warning can be ignored as we mentioned earlier that since this is a self-signed certificate, we will not have SSL 
stapling. If your output is as above, we can proceed to restart Nginx so as to ensure our changes are implemented.
We can type this:

```bash
sudo sysmtemctl restart nginx
```

We now need to test that our encryption is working and to do this, you can open your web broswer and type `https://`
followed by your server's IP address or domain name in the address bar

```bash
https://server_domain_or_IP
```

Since our certificate is self-signed, it  will not be recognized by your browser's trusted certificate authorities, 
hence you will get a warning in your browser when accesing your site. This is normal and expected.

If the redirect worked fine, we can now change the Nginx configuration file to ensure that only encrypted traffic is
received. Open the Nginx configuration file.

```bash
sudo nano /etc/nginx/sites-available/your-filename
```
Replace `your-filename` with the correct name of your configuration file. In the configuration file, find the 
`retutn 302` and change it to `return 301` then save and close the file. We then need to check for any syntax errors in
the configuration file.

```bash
sudo nginx -t
``` 
If no errors arise, then we restart Nginx to make the https redirect permanent

```bash
sudo systemctl nginx restart
```

With these configurations in place we can now change a url form http to https using a self-signed ssl certificate.
