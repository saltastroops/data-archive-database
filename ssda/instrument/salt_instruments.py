import pandas as pd
from astropy.coordinates import Angle
from typing import List, Optional, Any
from ssda.connection import sdb_connect
from datetime import date, datetime, timedelta
from ssda.instrument.instrument_fits_data import (
    Target,
    PrincipalInvestigator,
    DataCategory
)

from ssda.observation_status import ObservationStatus


class SALTInstruments:
    @staticmethod
    def data_category(object_name) -> DataCategory:
        """
         The category (such as science or arc) of the data contained in the FITS file.

         Returns
        -------
        category : DataCategory
            The data category.
        """
        if object_name.upper() == "ARC":
            return DataCategory.ARC
        elif object_name.upper() == "BIAS":
            return DataCategory.BIAS
        elif object_name.upper() == "FLAT":
            return DataCategory.FLAT
        else:
            return DataCategory.SCIENCE

    @staticmethod
    def preprocess_header_value(keyword: str, value: str) -> Any:
        """
        Preprocess a FITS header value for use in the database.

        Parameters
        ----------
        keyword : str
            FITs header keyword
        value : str
            FITS header value

        Returns
        -------
        preprocessed : Any
            The preprocessed value.

        """

        if keyword.upper() == 'GAIN':
            return SALTInstruments.gain(value)
        else:
            return value

    @staticmethod
    def gain(all_gains: str) -> Optional[float]:
        """
        The average of gain values from a FITS header value.

        Parameters
        ----------
        all_gains : Optional[str]
            FITS header value with a list of gain values

        Returns
        -------
        gain : float
            The average gain value.

        """

        if all_gains is None or all_gains == "":
            return None
        list_gains = all_gains.split()
        try:
            gain_sum = sum([float(gain) for gain in list_gains])
            return gain_sum / len(list_gains)
        except:
            return None

    @staticmethod
    def investigator_ids(proposal_code):
        """
        The list of ids of users who are an investigator on the proposal for the FITS
        file.

        The ids are those assigned by the institution (such as SALT or the SAAO) which
        received the proposal. These may differ from ids used by the data archive.

        An empty list is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        ids : list of id
            The list of user ids.

        """

        # Proposals without proposal code have no users
        if proposal_code is None:
            return []

        # Find the users
        salt_users_sql = """
                SELECT Username
                       FROM PiptUser
                       JOIN Investigator
                            ON PiptUser.Investigator_Id = Investigator.Investigator_Id
                       JOIN ProposalInvestigator
                            ON Investigator.Investigator_Id = ProposalInvestigator.Investigator_Id
                       JOIN ProposalCode
                            ON ProposalInvestigator.ProposalCode_Id = ProposalCode.ProposalCode_Id
                WHERE Proposal_Code=%s
                """
        salt_users_df = pd.read_sql(
            salt_users_sql, con=sdb_connect(), params=(proposal_code,)
        )

        return list(salt_users_df["Username"])

    @staticmethod
    def is_proprietary(proposal_code) -> bool:
        """
        Indicate whether the data for the FITS file is proprietary.

        Returns
        -------
        proprietary : bool
            Whether the data is proprietary.

        """

        # TODO: Will have to be updated
        sql = """
        SELECT ReleaseDate
               FROM ProposalGeneralInfo
               JOIN ProposalCode USING (ProposalCode_Id)
        WHERE Proposal_Code=%s
        """
        with sdb_connect().cursor() as cursor:
            cursor.execute(sql, (proposal_code,))
            result = cursor.fetchone()
            if result is None:
                return False
            public_from = result["ReleaseDate"]
            return public_from > datetime.now().date()

    @staticmethod
    def observation_status(block_visit_id: Optional[str]) -> ObservationStatus:
        """
        The status (such as Accepted) for the observation to which the FITS file
        belongs.

        If the FIS file is not linked to any observation, the status is assumed to be
        Accepted.

        Returns
        -------
        status : ObservationStatus
            The observation status.

        """

        if block_visit_id is None:
            return ObservationStatus.ACCEPTED

        sql = """
        SELECT BlockVisitStatus FROM BlockVisitStatus JOIN BlockVisit WHERE BlockVisit_Id=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(block_visit_id,))

        return ObservationStatus(df["BlockVisitStatus"][0])

    @staticmethod
    def principal_investigator(proposal_code) -> Optional[PrincipalInvestigator]:
        """
        The principal investigator for the proposal to which this file belongs.
        If the FITS file is not linked to any observation, the status is assumed to be
        Accepted.

        Returns
        -------
        pi : PrincipalInvestigator
            The principal investigator for the proposal.

        """

        if not proposal_code:
            return None

        sql = """
        SELECT FirstName, Surname
               FROM Investigator
               JOIN ProposalInvestigator
                    ON Investigator.Investigator_Id=ProposalInvestigator.Investigator_Id
               JOIN ProposalContact
                    ON ProposalInvestigator.Investigator_Id=ProposalContact.Leader_Id
               JOIN ProposalCode
                    ON ProposalContact.ProposalCode_Id=ProposalCode.ProposalCode_Id
        WHERE Proposal_Code=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(proposal_code,))
        if len(df) == 0:
            raise ValueError(
                "No Principal Investigator was found for the proposal {}".format(
                    proposal_code
                )
            )

        return PrincipalInvestigator(
            family_name=df["Surname"][0], given_name=df["FirstName"][0]
        )

    @staticmethod
    def proposal_code(code) -> Optional[str]:
        """
        The unique identifier of the proposal to which the FITS file belongs.

        The identifier is the identifier that would be used whe referring to the
        proposal communication between the Principal Investigator and another
        astronomer. For example, an identifier for a SALT proposal might look like
        2019-1-SCI-042.

        None is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        code : str
            The proposal code.

        """
        if code is None:
            return None

        # Is this a valid proposal code (rather than a fake one such as 'CAL_BIAS')?
        if code[:2] == "20":
            return code
        else:
            return None

    @staticmethod
    def proposal_title(proposal_code) -> Optional[str]:
        """
        The proposal title of the proposal to which the FITS file belongs.

        None is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        title : str
            The proposal title.

        """

        if not proposal_code:
            return None

        sql = """
        SELECT Title
               FROM ProposalText
               JOIN ProposalCode USING (ProposalCode_Id)
        WHERE Proposal_Code=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(proposal_code,))

        return df["Title"][0]

    @staticmethod
    def public_from(telescope_observation_id) -> date:
        """
        Indicate when the the became public.

        Returns
        -------
        date :
            When data became public.

        """

        # TODO: Will have to be updated
        sql = """
            SELECT ReleaseDate FROM Block
                JOIN Proposal ON( Block.Proposal_Id = Proposal.Proposal_Id)
                JOIN ProposalGeneralInfo ON (Proposal.ProposalCode_Id = ProposalGeneralInfo.ProposalCode_Id)
            WHERE Block_Id=%s
            """
        with sdb_connect().cursor() as cursor:
            cursor.execute(sql, (telescope_observation_id,))
            result = cursor.fetchone()
            if result is None:
                return (datetime.now()).date()
            public_from = result["ReleaseDate"]
            return public_from

    @staticmethod
    def target(
            ra_header_value: Optional[str],
            dec_header_value: Optional[str],
            block_visit_id: Optional[int],
            object_name: Optional[str]) -> Optional[Target]:
        """
        The target specified in the FITS file.

        None is returned if no target is specified, i.e. if no target position is
        defined.

        Returns
        -------
        target: Target
            The target

        """

        # Get the target position
        if ra_header_value and not dec_header_value:
            raise ValueError(
                "There is a right ascension header value, but no declination header value."
            )
        if not ra_header_value and dec_header_value:
            raise ValueError(
                "There is a declination header value, but no right ascension header value."
            )
        if not ra_header_value and not dec_header_value:
            return None
        ra = Angle("{} hours".format(ra_header_value)).degree
        dec = Angle("{} degrees".format(dec_header_value)).degree

        # Calibrations don't have a target
        if object_name.upper() in ["ARC", "BIAS", "FLAT"]:
            return None

        # Get the target type
        _target_type = SALTInstruments.target_type(block_visit_id)

        return Target(name=object_name, ra=ra, dec=dec, target_type=_target_type)

    @staticmethod
    def target_type(block_visit_id: Optional[int]) -> Optional[str]:
        """
        The type of target observed in a block visit.

        Parameters
        ----------
        block_visit_id : int
            The block visit id.

        Returns
        -------
        type : str
            The target type.

        """

        # No target type can be determined if there is no observation linked to the target
        if block_visit_id is None or block_visit_id:
            return None

        # Get the target type from the SDB
        sdb_target_type_query = """
        SELECT NumericCode
               FROM BlockVisit
               JOIN Pointing ON (BlockVisit.Block_Id=Pointing.Block_Id)
               JOIN Observation USING(Pointing_Id)
               JOIN Target USING(Target_Id)
               JOIN TargetSubType USING(TargetSubType_Id)
        WHERE BlockVisit_Id = %s
        """
        numeric_code_df = pd.read_sql(
            sql=sdb_target_type_query, con=sdb_connect(), params=(block_visit_id,)
        )
        if numeric_code_df.empty:
            return None

        return numeric_code_df["NumericCode"][0]
