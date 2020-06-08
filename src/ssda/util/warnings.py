from dataclasses import dataclass
from typing import List

_warnings: List[Warning] = []


def record_warning(warning: Warning):
    """
    Record a warning.

    Parameters
    ----------
    warning : Warning
        Warning to record.

    """

    _warnings.append(warning)


def get_warnings() -> List[Warning]:
    """
    Get the recorded warnings.

    Returns
    -------
    List[Warning]
        Recorded warnings.

    """

    return _warnings


def clear_warnings():
    """
    Clear the recorded warnings.

    """

    _warnings.clear()
