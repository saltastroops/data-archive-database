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
    print("DF:\n", df)
    print()
    print("TEl:\n", df['telescopeId'][0])
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


def get_last_observation_id():
    """
    Retrieves the observation id
    
    :return: int or None if does not exist
    """
    sql = """
        SELECT observationId FROM Observation ORDER BY observationId DESC LIMIT 1
    """
    
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
