from datetime import datetime
from connection import sdb_connect, ssda_connect


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
    :return: int
    """
    mydb = ssda_connect()

    cursor = mydb.cursor()

    cursor.execute("select id from Telescope where telescopeName =%s", (telescope_name,))
    record = cursor.fetchone()

    value = record[0]

    mydb.close()
    
    return value


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


def get_observation_status(status_id):
    mydb = ssda_connect()

    cursor = mydb.cursor()

    cursor.execute("select status from ObservationStatus where id =%s", (status_id,))
    record = cursor.fetchone()

    value = record[0]

    print(value)
    mydb.close()

    return


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
