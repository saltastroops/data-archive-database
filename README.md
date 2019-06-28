# Populating the SAAO/SALT Data Archive Database

This application lets you populate (and update) the SAAO/SALT Data Archive database.

## Installation and configuration

Ensure that Python 3.7 is running on your machine. You can check this with the `--version flag`.

```bash
python3 --version
```

If it is not installed on your machine already, [install pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv). One option for this is to use pip,

```bash
pip3 install pipenv
```

but you may also use Homebrew (on a Mac) or Lunuxbrew (on a Linux machine),

```bash
brew install pipenv
```

Then clone the package from its repository,

```bash
git clone https://github.com/saltastroops/data-archive-database.git
```

and make sure you are in the master branch,

```bash
git checkout master
```

You can then install all requirements with pipenv,

```bash
pipenv install --ignore-pipfile
```

Before using the package you need to define the following environment variables.

Variable name | Explanation | Example
--- | --- | ---
FITS_BASE_DIR | Base directory for the FITS files | /home/ssda/fits
PREVIEW_BASE_DIR | Base directory for the preview files | /home/ssda/preview
SDB_DATABASE | Name of SALT's science database | sdb
SDB_HOST | Host of SALT's science database | sdb.your.host
SDB_PASSWORD | Password for SALT's science database | secret
SDB_USER | Username for SALT science database | sdb_user
SSDA_DATABASE | Name of the Data Archive database | ssda
SSDA_HOST | Host of the Data Archive database | ssda.your.host
SSDA_PASSWORD | Password for the Data Archive database | also_secret
SSDA_USER | Password for the Data Archive database | ssda_user

See below for instructions on how to run the script as a cron job.

## Setting up the database

If the database does not exist yet, you can create it with the SQL script in `sql/tables.sql`.

```bash
mysql -u <admin_user> -h <host> -p < sql/tables.sql
```

Be careful with running the script - if the database exists its tables will be dropped and recreated.

## Upgrading

In order to upgrade the script, make sure you are in the master branch

```bash
git checkout master
```

and pull the changes from the remote repository,

```bash
git pull
```

As requirements may have changed, you should upgrade the installed packages afterwards.

```bash
pipenv install
```

## Usage

The package provides a script `cli.py` for inserting, updating and deleting entries in the Data Archive database. To run this script, first open a new pipenv shell.

```bash
pipenv shell
```

To find out about the available subcommands you may use the `--help` option.

```bash
python cli.py --help
``` 

The various subcommands for modifying the database are explained in the following sections.

If you don't want ro open a new shell you may also execute the script with pipenv's `run` command.

```bash
pipenv run python cli.py --help
```

### The insert subcommand

The `insert` subcommand allows you to create new database entries from FITS files. This includes corresponding preview files. Typically you use it to create entries for a range of dates.

```bash
python cli.py insert --start 2019-06-25 --end 2019-06-27
```

Both start and end date must be given, and they must be of the format `yyyy-mm-dd`. Both the start and end date are inclusive, and they refer to the beginning of the night. So in the above example FITS files would be considered for the time between noon of 25 June and noon of 28 June 2019. If you want to insert entries for one night, the start and end date must be the same.

```bash
python cli.py insert --start 2019-07-03 --end 2019-07-03
```

For convenience, you may use the keyword 'yesterday', which will be replaced with (gasp!) yesterday's date.

```bash
python cli.py insert --start yesterday --end yesterday
```

Another choice is the keyword `last-year`, which means 365 days ago, irrespective of whether the year had 365 or 366 days.

```bash
python cli.py insert --start last-year --end yesterday
```

This keyword is mostly intended for updating obsercvation status values and proposal investigators.

Existing database content is not changed by this subcommand; use the `update` subcommand to make changes. This implies that it is safe to re-run the command as often as you like.

By default FITS files for all instruments are considered. However, you can limit insertions to a single instrument by adding the `--instrument` option.

```bash
python cli.py insert --start 2019-06-29 --end 2019-07-02 --instrument RSS
```

The spelling of the instrument name is case-insensitive. Hence you might also have riun the command as

```bash
python cli.py insert --start 2019-06-29 --end 2019-07-02 --instrument rss
```

You can limit insertion to a set of instruments by using the `--instrument` option more than once.

```bash
python cli.py insert --start 2019-06-29 --end 2019-07-02 --instrument RSS --instrument Salticam
```

If you want to create an entry for a single FITS file, you can use the `--file` option. You then need to also specify the instrument for the FITS file with the `--instrument` option. *It is up to you to ensure that the specified instrument is correct; doom and disaster may strike if you get this wrong.* You have been warned.

The `--start/--end` and `--file` option are mutually exclusive.

While by default the subcommand does its job in absolute silence (unless there is an error), you can make the script morec talkative by adding the `--verbose` flag.

You can remind yourself about the usage of the subcommand by running it with the `--help` flag.

```bash
ssda insert --help
```

### The update subcommand

The `update` subcommand updates existing database entries and any corresponding preview files from FITS files. The usage is the same as that for the `insert` subcommand. For example, you would update all the database entries for HRS from the nights of 5 July to 10 July 2019 by running

```bash
python cli.py update --start 2019-07-05 --end 2019-07-10 --instrument HRS
```

The subcommand does not create entries for files not covered by the database yet. Instead it will abort with an error if it encounters such a file.

By default all information related to a FITS file is updated. However, this can be limited with the `--scope` option to the observation status values,

```bash
python cli.py update --start 2019-07-05 --end 2019-07-10 --scope observation-status
```

or the proposal investigators,

```bash
python cli.py update --start 2019-07-05 --end 2019-07-10 --scope investigator
```

### The delete subcommand

You can use the `delete` subcommand to delete database entries and their corresponding preview files. The usage is the same as for the `insert` subcommand. For example, the following command will delete all database entries for the night starting on 8 June 2019.

```bash
python cli.py delete --start 2019-06-08 --end 2019-06-08
``` 

The subcommand prompts you for a confirmation that you really want to delete database entries (and preview files). You can use the `--force` flag to skip this.

### Subcommand options

As explained in the previous subsections, the `ssda` subcommands accept the following options.

Option | Explanation
--- | ---
--end | Start date of the last night for which data is considered.
--file | Use this FITS file.
--force | Don't ask for confirmation before running the `delete` subcommand.
--instrument | Instrument whose FITS files shall be considered. This option may be used multiple times unless the `--file` flag is used.
-h / --help | Display a help message.
--scope | The scope of updates. This can be `all`, `observation-status` or `investigator`. `all` is the default.
--start | Start date of the first night for which data is considered.

Generally these options are available for all the subcommands. The only exceptions are `--force` (only used with `delete`) and `--scope` (only used with `update`).

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
8 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose update --start last-year --end yesterday --scope observation-status > $SSDA_LOG 2>&1
9 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose update --start last-year --end yesterday --scope investigator > $SSDA_LOG 2>&1
10 * * * source .bashrc; cd /home/ssda/applications/database-update; pipenv run python cli.py --verbose insert --start yesterday --end yesterday > $SSDA_LOG 2>&1
```

## Extending the code

### Using an additional Python library

If you need to make use of a new Python library, you need to install it with `pipenv`.

```bash
pipenv install new_paqckage
```

If the new package is needed for development only, you should use the `--dev` glag when installing it.

```bash
pipenv install --dev new_package
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
from ssda.instrument.hrs_fits_data import HrsFitsData
from ssda.instrument.isibane_fits_data import IsidibaneFitsData
from ssda.instrument.rss_fits_data import RssFitsData
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
