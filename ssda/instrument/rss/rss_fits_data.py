from datetime import date, datetime

from astropy.coordinates import Angle
from dateutil import parser
import glob
import os
import pandas as pd
from typing import List, Optional

from ssda.connection import sdb_connect
from ssda.instrument.instrument_fits_data import (
    InstrumentFitsData,
    PrincipalInvestigator,
    Target,
    DataCategory,
    Institution,
)
from ssda.observation_status import ObservationStatus
from ssda.telescope import Telescope

from ssda.imaging import save_image_data


class RssFitsData(InstrumentFitsData):
    def __init__(self, fits_file: str):
        InstrumentFitsData.__init__(self, fits_file)

    @staticmethod
    def fits_files(night: date) -> List[str]:
        """
        The list of FITS files generated for the instrument during a night.

        Parameters
        ----------
        night : date
            Start date of the night for which the FITS files are returned.

        Returns
        -------
        files : list of str
            The list of file paths.

        """

        data_directory = "{base_dir}/salt/{year}/{monthday}/rss/raw".format(
            base_dir=os.environ["FITS_BASE_DIR"],
            year=night.strftime("%Y"),
            monthday=night.strftime("%m%d"),
        )

        return sorted(glob.iglob(os.path.join(data_directory, "*.fits")))

    def create_preview_files(self) -> List[str]:
        """
        Create the preview files for the FITS file.

        Returns
        -------
        paths: list of str
            The list of file paths of the created preview files.

        """

        # Create the required directories
        salt_dir = os.path.join(os.environ["PREVIEW_BASE_DIR"], "salt")
        if not os.path.exists(salt_dir):
            os.mkdir(salt_dir)
        year_dir = os.path.join(salt_dir, str(self.night().year))
        if not os.path.exists(year_dir):
            os.mkdir(year_dir)
        day_dir = os.path.join(year_dir, self.night().strftime("%m%d"))
        if not os.path.exists(day_dir):
            os.mkdir(day_dir)
        rss_dir = os.path.join(day_dir, "rss")
        if not os.path.exists(rss_dir):
            os.mkdir(rss_dir)

        # Create the header content file
        basename = os.path.basename(self.file_path)[:-5]
        header_content_file = os.path.join(rss_dir, basename + "-header.txt")
        with open(header_content_file, "w") as f:
            f.write(self.header_text)
        preview_files = [header_content_file]

        # Create the image files
        preview_files += save_image_data(self.file_path, rss_dir)

        return preview_files

    def data_category(self) -> DataCategory:
        """
        The category (such as science or arc) of the data contained in the FITS file.

        Returns
        -------
        category : DataCategory
            The data category.

        """

        # TODO: What about standards?
        object_name = self.header.get("OBJECT").upper()
        if object_name == "ARC":
            return DataCategory.ARC
        elif object_name == "BIAS":
            return DataCategory.BIAS
        elif object_name == "FLAT":
            return DataCategory.FLAT
        else:
            return DataCategory.SCIENCE

    def institution(self) -> Institution:
        """
        The institution (such as SALT or SAAO) operating the telescope with which the
        data was taken.

        Returns
        -------
        institution : Institution
            The institution.

        """

        return Institution.SALT

    def instrument_details_file(self) -> str:
        """
        The path of the file containing FITS header keywords and corresponding columns
        of the instrument table.

        The format of the file content must be as follows:

        - Lines starting with a '#' are comments.
        - Lines containing only whitespace are comments.
        - Any non-comment line has a FITS header keyword and a datavase column,
          separated by whitespace.

        For example:

        # First column is for FITS header keywords
        # Second column is for table columns

        AMPSEC         amplifierSection
        AMPTEM         amplifierTemperature
        ATM1_1         amplifierReadoutX
        ATM1_2         amplifierReadoutY

        Returns
        -------
        path : str
            The file path.

        """

        directory = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(directory, "rss_keywords.txt")

    def instrument_id_column(self) -> str:
        """
        The name of the column containing the id (i.e. the primary key) in the table
        containing the instrument details for the instrument that took the data.

        Returns
        -------
        column : str
            The column name.

        """

        return "rssId"

    def instrument_table(self) -> str:
        """
        The name of the table containing the instrument details for the instrument that
        took the data.

        The primary key column of the table must the string you get when concatenating
        the table name in lower case and 'Id'. For example, for the RSS table this
        column must be named rssId.

        Returns
        -------
        table : str
            The name of the instrument details table.

        """

        return "RSS"

    def investigator_ids(self) -> List[str]:
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
        proposal_code = self.proposal_code()
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

    def is_proprietary(self) -> bool:
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
            cursor.execute(sql, (self.proposal_code(),))
            result = cursor.fetchone()
            if result is None:
                return False
            release_date = result["ReleaseDate"]
            return release_date > datetime.now().date()

    def night(self) -> date:
        """
        The night when the data was taken.

        Returns
        -------
        night : date
            The date of the night when the data was taken.

        """

        return parser.parse(self.header.get("DATE-OBS")).date()

    def observation_status(self) -> ObservationStatus:
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

        block_visit_id = self.telescope_observation_id()
        if block_visit_id is None:
            return ObservationStatus.ACCEPTED

        sql = """
        SELECT BlockVisitStatus FROM BlockVisitStatus JOIN BlockVisit WHERE BlockVisit_Id=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(block_visit_id,))

        return ObservationStatus(df["BlockVisitStatus"][0])

    def principal_investigator(self) -> Optional[PrincipalInvestigator]:
        """
        The principal investigator for the proposal to which this file belongs.
        If the FITS file is not linked to any observation, the status is assumed to be
        Accepted.

        Returns
        -------
        pi : PrincipalInvestigator
            The principal investigator for the proposal.

        """

        proposal_code = self.proposal_code()
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

    def proposal_code(self) -> Optional[str]:
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

        code = self.header.get("PROPID") or None
        if not code:
            return None

        # Is this a valid proposal code (rather than a fake one such as 'CAL_BIAS')?
        if code[:2] == "20":
            return code
        else:
            return None

    def proposal_title(self) -> Optional[str]:
        """
        The proposal title of the proposal to which the FITS file belongs.

        None is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        title : str
            The proposal title.

        """

        proposal_code = self.proposal_code()
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

    def start_time(self) -> datetime:
        """
        The start time, i.e. the time when taking data for the FITS file began.

        Returns
        -------
        time : datetime
            The start time.

        """

        return parser.parse(self.header["DATE-OBS"] + " " + self.header["TIME-OBS"])

    def target(self) -> Optional[Target]:
        """
        The target specified in the FITS file.

        None is returned if no target is specified, i.e. if no target position is
        defined.

        Returns
        -------

        """

        # Get the target position
        ra_header_value = self.header.get("RA")
        dec_header_value = self.header.get("DEC")
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

        # Get the target name
        name = self.header.get("OBJECT", "")

        # Calibrations don't have a target
        if name.upper() in ["ARC", "BIAS", "FLAT"]:
            return None

        # Get the target type
        _target_type = target_type(self.header.get("BVISITID"))

        return Target(name=name, ra=ra, dec=dec, target_type=_target_type)

    def telescope(self) -> Telescope:
        """
        The telescope used for observing the data in the FITS file.

        Returns
        -------
        telescope : Telescope
            The telescope.

        """

        return Telescope.SALT

    def telescope_observation_id(self) -> str:
        """
        The id used by the telescope for the observation.

        If the FITS file was taken as part of an observation, this method returns the
        unique id used by the telescope for identifying this observation.

        If the FITS file was not taken as part of an observation (for example because it
        refers to a standard), this method returns None.

        Returns
        -------
        id : str
            The unique id used by the telescope for identifying the observation.

        """

        return self.header.get("BVISITID") or None


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
