from ssda.instrument.salt_imaging_camera_observation_properties import SaltImagingCameraObservationProperties
from ssda.util import types
from typing import Optional


class BCAMObservationProperties(SaltImagingCameraObservationProperties):
    def observation(
            self, observation_group_id: Optional[int], proposal_id: Optional[int]
    ) -> types.Observation:
        return self.salt_observation.observation(
            observation_group_id=observation_group_id,
            proposal_id=proposal_id,
            instrument=types.Instrument.BCAM,
        )
