from dataclasses import dataclass
from typing import Optional
from ssda.util.fits import StandardFitsFile


@dataclass
class LogData:
    block_visit_id: Optional[str]
    object: Optional[str]
    observation_mode: Optional[str]
    observation_time: Optional[str]
    observation_type: Optional[str]
    path: Optional[str]
    proposal_code: Optional[str]

    def is_daytime_observation(self):
        """
        Is this an observation taken between 6:00 and 15:00 UTC?

        If the observation time cannot be found, it is assumed that the observation is
        not a daytime one.

        Returns
        -------
        bool
            Whether this is a daytime observation.

        """

        try:
            parts = self.observation_time.strip().split(":")
            if len(parts) > 1:
                return 6 <= int(parts[0]) < 15
        except:
            return False


def get_salt_data_to_log(path: str) -> LogData:
    fits_file = StandardFitsFile(path)
    log_data = LogData(
        path=str(path),
        proposal_code=fits_file.header_value("PROPID"),
        block_visit_id=fits_file.header_value("BVISITID"),
        observation_type=fits_file.header_value("OBSTYPE"),
        observation_mode=fits_file.header_value("OBSMODE"),
        object=fits_file.header_value("OBJECT"),
        observation_time=fits_file.header_value("TIME-OBS"),
    )
    return log_data
