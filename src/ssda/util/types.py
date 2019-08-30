from __future__ import annotations
import os
from datetime import date
from enum import Enum

from astropy.units import def_unit


_bytes = def_unit("bytes")


class DatabaseConfiguration:
    """
    A database configuration.

    Parameters
    ----------
    host : str
        Domain of the host server (such as 127.0.0.1 or db.your.host)
    username : str
        Username of the database user.
    password : str
        Password of the database user.
    database : str
        Name of the database.
    port : int
        Port number.

    """

    def __init__(
        self, host: str, username: str, password: str, database: str, port: int
    ) -> None:
        if port <= 0:
            raise ValueError("The port number must be positive.")

        self._host = host
        self._username = username
        self._password = password
        self._database = database
        self._port = port

    def host(self) -> str:
        """
        The domain of the host server.

        Returns
        -------
        str
            The host server.

        """

        return self._host

    def username(self) -> str:
        """
        The username of the database user.

        Returns
        -------
        str
            The database user.

        """

        return self._username

    def password(self) -> str:
        """
        The password of the database user.

        Returns
        -------
        str
            The password.

        """

        return self._password

    def database(self) -> str:
        """
        The name of the database.

        Returns
        -------
        str
            The name of the database.

        """

        return self._database

    def port(self) -> int:
        """
        The port number.

        Returns
        -------
        int
            The port number.

        """

        return self._port

    def __eq__(self, other: DatabaseConfiguration):
        return (
            self.host() == other.host()
            and self.username() == other.username()
            and self.password() == other.password()
            and self.database() == other.database()
            and self.port() == other.port()
        )


class DateRange:
    """
    A date range.

    The start date is inclusive, the end date exclusive. So, for example, if the start
    date is 1 January 2019 and the end date 4 January 2019, the date range contains
    1 January, 2 January and 3 January, but not 4 January 2019.

    The start date must be earlier than the end date.

    Parameters
    ----------
    start : date
        Start date.
    end : date
         End date.

    Raises
    ------
    ValueError
        If the start date is equal to or later than the start date.

    """

    def __init__(self, start: date, end: date) -> None:
        if start >= end:
            raise ValueError("The start date must be earlier than the end date.")

        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        """
        The start date.

        Returns
        -------
        date
            The start date.

        """

        return self._start

    @property
    def end(self) -> date:
        """
        The end date.

        Returns
        -------
        date
            The end date.

        """

        return self._end


class FilePath:
    def __init__(self, path: str) -> None:
        """
        A file path of an existing regular file.

        Parameters
        ----------
        path : str
            File path.

        Raises
        ------
        ValueError
            If the file path does not exist or is not a regular file.

        """

        if not os.path.isfile(path):
            raise ValueError("Not a regular file: ")

        self._path = path

    @property
    def path(self) -> str:
        """
        The file path.

        Returns
        -------
        str
            The file path.

        """

        return self._path


class Instrument(Enum):
    """
    Enumeration of the instruments.

    The enum values must be the same as the values of the instrumentName column in the
    Instrument table.

    """

    RSS = "RSS"
    HRS = "HRS"
    SALTICAM = "Salticam"

    @staticmethod
    def for_name(name: str) -> Instrument:
        """The instrument for a case-insensitive name.

        Parameters
        ----------
        name : str
            Instrument name.

        Returns
        -------
        Instrument :
            Instrument.

        """

        for instrument in Instrument:
            if name.lower() == str(instrument.value).lower():
                return instrument

        raise ValueError(f"Unknown instrument name: {name}")


class TaskName(Enum):
    """
    Enumeration of the task names.

    """

    DELETE = "delete"
    INSERT = "insert"

    @staticmethod
    def for_name(name: str) -> TaskName:
        """The task name for a case-insensitive name.

        Parameters
        ----------
        name : str
            Task name.

        Returns
        -------
        TaskName :
            Task name.

        """

        for task_name in TaskName:
            if name.lower() == str(task_name.value).lower():
                return task_name

        raise ValueError(f"Unknown task name: {name}")


class TaskExecutionMode(Enum):
    """
    Enumeration of the task execution modes.

    """

    DUMMY = "dummy"
    PRODUCTION = "production"

    @staticmethod
    def for_mode(mode: str) -> TaskExecutionMode:
        """The task execution mode for a case-insensitive mode.

        Parameters
        ----------
        mode : str
            Task execution mode.

        Returns
        -------
        TaskExecutionMode
            Task execution mode.

        """

        for task_mode in TaskExecutionMode:
            if mode.lower() == str(task_mode.value).lower():
                return task_mode

        raise ValueError(f"Unknown task execution mode: {mode}")


class Telescope(Enum):
    """
    Enumeration of the telescopes included in the SSDA.

    The enum values must be the same as the telescope names in the Telescope table.

    """

    LESEDI = "LESEDI"
    ONE_DOT_NINE = "1.9 m"
    SALT = "SALT"
