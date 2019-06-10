from datetime import datetime

from connection import sdb_connect, ssda_connect
import pandas as pd


# Get the telescopeName, given a telescopeID
def get_telescope_name(telescope_id):
    mydb = sdb_connect()

    cursor = mydb.cursor()

    cursor.execute("select telescopeName from Telescope where id =%s", (telescope_id,))
    record = cursor.fetchone()

    value = record[0]

    "this prints a passed string into this function"
    print(value)
    mydb.close()
    return


def get_target_id(target_name, right_ascension, declination):
    sql = """
    SELECT targetId FROM BlockVisit WHERE name=%s AND rightAscension=%s AND declination=%s
"""

    df = pd.read_sql(sql, con=sdb_connect(), params=(target_name, right_ascension, declination))

    if df.empty:
        return None

    return int(df['targetId'][0])


def get_data_file_id(filename):
    """

    :param filename:
    :return: datafile Id
    """

    sql = """
                SELECT dataFileId FROM DataFile WHERE name=%s
            """

    df = pd.read_sql(sql, con=sdb_connect(), params=(filename))

    if df.empty:
        return None

    return int(df['dataFileId'][0])


def get_target_type_id(block_id):
    """
    Get the target type id from SSDA.
    Given that all target types are predefined on SSDA
    :param block_id: SBD block id
    :return: target type id.
    """
    if block_id is None:
        return None
    sdb_target_type_query = """
SELECT NumericCode from Pointing as p
    JOIN Observation USING(Pointing_Id)
    JOIN Target USING(Target_Id)
    JOIN TargetSubType USING(TargetSubType_Id)
WHERE Block_Id = %s
    """

    numeric_code_df = pd.read_sql(sql=sdb_target_type_query, con=sdb_connect(), params=block_id)
    if numeric_code_df.empty:
        return None

    numeric_code = numeric_code_df['NumericCode'][0]
    sql = """
SELECT targetTypeId FROM TargetType WHERE numericValue = %s
    """.format(numeric_code=numeric_code)
    numeric_code_id_df = pd.read_sql(sql=sql, con=ssda_connect(), params=numeric_code)
    if numeric_code_id_df.empty:
        return None

    return int(numeric_code_id_df['targetTypeId'][0])


# def get_target_type_from_sdb():


def get_telescope_id(telescope_name):
    """
    Retrieves the telescope id given a telescope name
    
    :param telescope_name: The telescope name e.g. SALT
    :return: int or None if does not exist
    """
    sql = """
        SELECT telescopeId from Telescope where telescopeName =%s
    """
    
    df = pd.read_sql(sql, con=ssda_connect(), params=(telescope_name,))

    if df.empty:
        return None

    return int(df['telescopeId'][0])


def get_data_category_id(data_category_name):
    """
    Retrieves the data category id given a data category name
    
    :param data_category_name: The data category name e.g. Bias
    :return: int or None if does not exist
    """
    sql = """
        SELECT dataCategoryId from DataCategory where dataCategory =%s
    """
    
    df = pd.read_sql(sql, con=ssda_connect(), params=(data_category_name,))
    
    if df.empty:
        return None
    
    return int(df['dataCategoryId'][0])


def get_observation_id(teleObsID, teleID):
    """
    Retrieves the observation id
    
    :return: int or None if does not exist
    """
    sql = """
        SELECT observationId FROM Observation WHERE telescopeObservationId={teleObsID} AND telescopeId={teleID} ORDER BY observationId DESC LIMIT 1
    """.format(teleObsID=teleObsID, teleID=teleID)
    
    df = pd.read_sql(sql, con=ssda_connect())
    
    if df.empty:
        return None
    
    return int(df['observationId'][0])


def get_last_data_file_id():
    """
    Retrieves the data file id
    
    :return: int or None if does not exist
    """
    sql = """
        SELECT dataFileId FROM DataFile ORDER BY dataFileId DESC LIMIT 1
    """
    
    df = pd.read_sql(sql, con=ssda_connect())
    
    if df.empty:
        return None
    
    return int(df['dataFileId'][0])


def get_last_target_id():
    """
    Retrieves the last target id
    
    :return: int or None if does not exist
    """
    sql = """
        SELECT targetId FROM Target ORDER BY targetId DESC LIMIT 1
    """
    
    df = pd.read_sql(sql, con=ssda_connect())
    
    if df.empty:
        return None
    
    return int(df['targetId'][0])


# Get the proposal information from the SDB
def proposal_details():
    # Populating the Proposal table

    now = datetime.now()

    # MySQL Connection to sdb
    sdb_connection = sdb_connect()
    sdb_cursor = sdb_connection.cursor()

    # MySQL Connection to ssda
    ssda_connection = ssda_connect()
    ssda_cursor = ssda_connection.cursor()

    # Get the result set with the needed parameters for populating the Proposal Table on the ssda database.
    sdbsql_select = "select distinctrow  ProposalCode.Proposal_Code, Investigator.FirstName, Investigator.Surname, \
            ProposalText.title\
           from ProposalCode  \
           join ProposalText  on ProposalCode.ProposalCode_Id = ProposalText.ProposalCode_Id \
           inner join ProposalInvestigator on ProposalCode.ProposalCode_Id = ProposalInvestigator.ProposalCode_Id \
           inner join Investigator on Investigator.Investigator_Id = ProposalInvestigator.Investigator_Id group by \
                    ProposalCode.ProposalCode_Id"

    # Execute the select query
    sdb_cursor.execute(sdbsql_select)

    # Grab the query result in a tuple
    sbdsql_result = sdb_cursor.fetchall()

    # Run through the results and insert into Proposal Table ssda database.
    for x in sbdsql_result:
        ssda_insert_sql = "insert into Proposal (proposalCode,principalInvestigatorGivenName, \
                          principalInvestigatorFamilyName,title, lastUpdated )  values(%s,%s,%s,%s,%s)"
        val = (x[0], x[1], x[2], x[3], now)

        # Execute the insert query
        ssda_cursor.execute(ssda_insert_sql, val)

    # Write the entries to the database.
    ssda_connection.commit()

    # Close database connections
    ssda_connection.close()
    sdb_connection.close()
    return


def get_observation_status_id(block_id):
    """
    Retrieves the observation status id of a given block id
    
    :param block_id:
    :return: int or None if does not exist
    """
    
    sql = """
        SELECT BlockStatus_Id from Block where Block_Id =%s
    """

    df = pd.read_sql(sql, con=sdb_connect(), params=(block_id,))
    
    if df.empty:
        return None
    
    return int(df['BlockStatus_Id'][0])


def get_telescope_observation_id(block_id):
    """
    Retrieves the telescope observation id of a given block id (BlockVisit_Id for the SALT telescope)
    
    :param block_id:
    :return: int or None if does not exist
    """
    
    sql = """
        SELECT BlockVisit_Id from BlockVisit where Block_Id =%s
    """
    
    df = pd.read_sql(sql, con=sdb_connect(), params=(block_id,))
    
    if df.empty:
        return None
    
    return int(df['BlockVisit_Id'][0])


def get_category_id(category):
    mydb = ssda_connect()

    cursor = mydb.cursor()

    cursor.execute("select id from DataCategory where dataCategory =%s", (category,))
    record = cursor.fetchone()

    value = record[0]

    print(value)
    mydb.close()
    return


def data_files(start_time):
    mydb = ssda_connect()

    cursor = mydb.cursor()

    cursor.execute("select name from DataFile where startTime =%s", (start_time,))
    record = cursor.fetchone()

    value = record[0]

    print(value)
    mydb.close()
    return


# Define what is meant by fits_headers
def observation_details(fits_headers):
    mydb = ssda_connect()

    cursor = mydb.cursor()

    cursor.execute("select telescopeObservationId, name, status  from Observation where startTime =%s", (fits_headers,))
    record = cursor.fetchone()

    value = record[0]

    print(value)
    mydb.close()

    return


def create_observation(telescope, telescope_observation_id=None, observation_status_id=1):
    """
    Create a SSDA observation.
    :param telescope: Telescope name
    :param telescope_observation_id: Block id for salt
    :param observation_status_id: Block status for salt
    :return:
    """
    # with an assumption that observation_status_id=1 is SUCCESSFUL
    conn = ssda_connect()
    cursor = conn.cursor()

    telescope_id = get_telescope_id(telescope)
    observation_sql = """
INSERT INTO Observation (telescopeId, telescopeObservationId, observationStatusId)
    SELECT * FROM (SELECT %s, %s, %s) as tmp
WHERE NOT EXISTS (
    SELECT telescopeId, telescopeObservationId
        FROM Observation
    WHERE telescopeId=%s AND telescopeObservationId=%s
) LIMIT 1;
"""
    params = (telescope_id, telescope_observation_id, observation_status_id, telescope_id, telescope_observation_id)
    cursor.execute(observation_sql, params)
    conn.commit()


def create_target(target_name, right_ascension, declination, block_id):
    conn = ssda_connect()
    cursor = conn.cursor()
    target_type_id = get_target_type_id(block_id)

    target_sql = """

INSERT INTO Target (name, rightAscension, declination, position, targetTypeId)
    SELECT * FROM (SELECT %s, %s, %s, POINT(%s, %s) , %s) as tmp
WHERE NOT EXISTS (
    SELECT name, rightAscension, declination, targetTypeId
        FROM Target
    WHERE name=%s AND rightAscension=%s AND declination=%s AND targetTypeId=%s
) LIMIT 1;
"""

    params = (
        target_name,
        right_ascension,
        declination,
        right_ascension,
        declination,
        target_type_id,
        target_name,
        right_ascension,
        declination,
        target_type_id
    )
    cursor.execute(target_sql, params)
    conn.commit()
    return True


def populate_target_type():
    """
    Get the target Type from SDA and store then in SSDA

    N.B> this method should only be ran once
    :return: None
    """
    conn = ssda_connect()
    cursor = conn.cursor()
    get_sql = """SELECT * from TargetSubType;"""

    insert_sql = "INSERT INTO TargetType (numericValue, explanation) VALUES "

    get_results = pd.read_sql(get_sql, sdb_connect())
    for i, row in get_results.iterrows():
        insert_sql += '("{numericValue}", "{explanation}"),\n'\
            .format(numericValue=row["NumericCode"], explanation=row["TargetSubType"])

    cursor.execute(insert_sql[:-2] + ";")
    conn.commit()


def get_ssda_observation_id(telescope_id, telescope_observation_id):
    """
    Retrieves the observation_id

    :return: int or None if does not exist
    """

    if telescope_observation_id is None:
        sql = """
        SELECT observationId FROM Observation ORDER BY observationId DESC LIMIT 1
            """
        df = pd.read_sql(sql=sql, con=ssda_connect())
    else:
        params = (telescope_observation_id, telescope_id)
        sql = """
            SELECT observationId FROM Observation WHERE telescopeObservationId=%s AND telescopeId=%s ORDER
            BY observationId DESC LIMIT 1
        """

        df = pd.read_sql(sql=sql, con=ssda_connect(), params=params)

    if df.empty:
        return None

    return int(df['observationId'][0])


def create_data_preview(name, datafile_id, order="DESC"):
    """

    :param name: Path to the file
    :param datafile_id: Identifier of the data file to which this preview belongs.
    :param order: Defines an order within multiple preview files for the same data file
    :return: None
    """
    conn = ssda_connect()
    cursor = conn.cursor()
    data_preview_sql = """
INSERT INTO DataPreview(
        name,
        dataFileId,
        orders
    )
    VALUES (%s,%s,%s)
"""
    data_preview_params = (
        name,
        datafile_id,
        order
    )
    cursor.execute(data_preview_sql, data_preview_params)


def remove_file_if_exist(filename):

    conn = ssda_connect()
    cursor = conn.cursor()

    get_file_data_sql = """
SELECT dataFileId FROM DataFile WHERE name=%s
    """
    df = pd.read_sql(sql=get_file_data_sql, con=ssda_connect(), params=(filename,))

    if df.empty:
        return

    data_file_id = int(df['dataFileId'][0])

    remove_data_file_sql = """
DELETE FROM DataFile WHERE dataFileId=%s
    """
    cursor.execute(sql=remove_data_file_sql, con=ssda_connect(), params=(data_file_id,))

    remove_data_preview_sql = """
    DELETE FROM DataPreview WHERE dataFileId=%s
        """
    cursor.execute(sql=remove_data_preview_sql, con=ssda_connect(), params=(data_file_id,))

    conn.commit()


def create_data_file(data_category_id, observation_date, filename, target_id, observation_id, file_size=None):
    """
    Create a data file for SSDA
    :param data_category_id: The data category id. This links to the DataCategory table.
    :param observation_date: The time when the data taking started, if the data set is a FITS file.
    :param filename: Name of the file, which must be unique.
    :param target_id: The id of the target which was observed. This links to the Target table.
    :param observation_id: The id of the observation to which the data set belongs.
    :param file_size: The file size in bytes.
    :return: None
    """
    remove_file_if_exist(filename)
    conn = ssda_connect()
    cursor = conn.cursor()
    data_files_sql = """
INSERT INTO DataFile(
    dataCategoryId,
    startTime,
    name,
    targetId,
    size,
    observationId
)
VALUES (%s,%s,%s,%s,%s,%s)
"""

    data_files_params = (
        data_category_id,
        observation_date,
        filename,
        target_id,
        file_size,
        observation_id
    )
    cursor.execute(data_files_sql, data_files_params)
    conn.commit()