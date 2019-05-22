def name_to_header(name):
    n = name.lower()
    if n == "date":
        return ""
    if n == 'block_id' or n == "observation_id":
        return "BLOCKID"
    if n == 'pi' or n == "principal_investigator" or n == "principal investigator" or n == "proposer":
        return "PROPOSER"


    return None
