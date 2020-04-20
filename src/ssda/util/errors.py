import os
from dataclasses import dataclass
from ssda.util.fits import StandardFitsFile


@dataclass
class LogData:
    block_visit_id: str
    filename: str
    object: str
    observation_mode: str
    observation_time: str
    observation_type: str
    proposal_code: str


def get_salt_data_to_log(path: str) -> LogData:
    fits_file = StandardFitsFile(path)
    log_data = LogData(
        filename=os.path.basename(path),
        proposal_code=fits_file.header_value("PROPID"),
        block_visit_id=fits_file.header_value("BVISITID"),
        observation_type=fits_file.header_value("OBSTYPE"),
        observation_mode=fits_file.header_value("OBSMODE"),
        object=fits_file.header_value("OBJECT"),
        observation_time=fits_file.header_value("TIME-OBS"),
    )
    return log_data
