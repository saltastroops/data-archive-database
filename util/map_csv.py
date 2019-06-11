from util.get_information import get_telescope_id
from util.util import handle_missing_header


def create_column_value_pair_from_headers(headers, data_file_id):

    filepath = \
        "/home/nhlavu/nhlavu/da/database/data-archive-database/telescope/salt/hrs/hrs_headers.csv" \
        if handle_missing_header(headers, "INSTRUME").lower() == "hrs" else \
        "/home/nhlavu/nhlavu/da/database/data-archive-database/telescope/salt/rss/rss_headers.csv" \
        if handle_missing_header(headers, "INSTRUME").lower() == "rss" else \
        "/home/nhlavu/nhlavu/da/database/data-archive-database/telescope/salt/salticam/scam_headers.csv" \
        if handle_missing_header(headers, "INSTRUME").lower() == "SALTICAM" else \
        None
    to_return = {}
    with open(filepath) as fp:
        line = fp.readline()

        while line:
            new = line.split()
            if len(line) > 0 and line[0] != "#" and len(new):
                to_return[new[1]] = handle_missing_header(headers, new[0])
            line = fp.readline()
    to_return["dataFileId"] = data_file_id
    return to_return


def create_insert_sql(table_map):
    columns = ""
    values = ""
    table = \
        "RSS" if table_map["instrumentName"].lower() == "rss" else \
        "HRS" if table_map["instrumentName"].lower() == "hrs" else \
        "Salticam" if table_map["instrumentName"].lower() == "salticam" else None
    for tableName, value in table_map.items():
        if value is not None:
            columns += '{tableName}, '.format(tableName=tableName)
            if isinstance(value, str):
                values += '"{value}", '.format(value=value)
            else:
                values += '{value}, '.format(value=str(value))

    sql = """
INSERT INTO {table}({columns}) VALUES ({values});
""".format(table=table, columns=columns[-2], values=values[-2])
    print("", sql)
    return sql
