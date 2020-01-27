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
flyway -url=jdbc:postgresql://your.host:5432/ssda -user=admin -locations=filesystem:sql migrate
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

If you want to create an entry for a single FITS file, you can use the `--file` option.

```bash
ssda --task insert --mode production --file /path/to/fits/files --instrument RSS
```

The `--start/--end` and `--file` option are mutually exclusive.

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
--file | Use this FITS file.
--fits-base-dir | Base directory containing all the FITS files.
--instrument | Instrument whose FITS files shall be considered. This option may be used multiple times unless the `--file` flag is used.
-h / --help | Display a help message.
--start | Start date (inclusive) of the date range to consider.
--skip-errors | Do not terminate if there is an error.

## Logging in verbose mode

If you want to log in verbose mode, you can use the `--verbose` option before the subcommand.

```bash
python cli.py --verbose insert --start yesterday --end yesterday
```

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
from ssda.instrument.instrument import IsidibaneFitsData
from ssda.instrument.instrument import RssFitsData
# ... other imports ...

class Instrument(Enum):
    HRS = "HRS"
    ISIBANE = "Isibane"
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
            return IsidibaneFitsData
        elif self == Instrument.RSS:
            return RssFitsData
        # ... elif clauses for other enum members ...
        else:
            raise ValueError('No InstrumentFitsData type found for {}'.format(self.value))
```

With these changes in place you can populate the database from the new instrument's FITS files, as you can for the previously existing instruments.

In order to update an instrument you just have to change the database tables and the above files as required.
