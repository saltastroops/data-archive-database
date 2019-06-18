# Populating the SAAO/SALT Data Archive Database

This package lets you populate (and update) the SAAO/SALT Data Archive database.

## Installation and configuration

Clone the package from its repository,

```bash
git clone https://github.com/saltastroops/data-archive-database.git
```

and make sure you are in the master branch,

```bash
git checkout master
```

You can then install the package with pip.

```bash
cd data-archive-database
pip install -e .
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

## Extending the code

### Using an additional Python library

If you need to make use of a new Python library, you need to add it to the requirements in the
`setup.py` file. In case the library is needed for development purposes only, you should instead add it to the `requirements-dev.txt` file. Either way, you'll have to install the package via pip.

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

### Adding a telescope

A new telescope must be added to the Telescope table in the SSDA database, and if it is owned by a new institution this institution needs to be added to the Institution table.

For example, in order to define a telescope called Ikhwezi, owned by the University of Wakanda, you would first run the following SQL statement,

```mysql
INSERT INTO Institution (institutionName) VALUES ('University of Wakanda')
```

and, assuming that the primary key of the new entry has the value 42, then run the following SQL statement,                                              `

```mysql
INSERT INTO Telescope (telescopeName, ownerId) VALUES ('Ikhwezi', 42)
```

Once the database has been updated, you should add the new telescope as an enum member to the `telescope` class in the file `src/ssda/telescope.py`.

```python
IKHWEZI = 'Ikhwezi'
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
