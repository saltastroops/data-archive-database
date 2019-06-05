from connection import ssda_connect
import pandas as pd


def handle_missing_header(header_obj, header):
    try:
        return None if str(header_obj[header]).lower() == "none" else header_obj[header]
    except KeyError:
        return None
    
    
def convert_time_to_float(time):
    if len(time) == 0:
        return None
    
    if len((time.split('-'))) > 1:
        if len(time.split(':')) == 1:
            (d) = time
            result = int(d) + 360
            
            return result
        if len(time.split(':')) == 2:
            (d, m) = time.split(':')
            result = ((int(d) + 360) + int(m)) * 60
            
            return result
        
        (d, m, s) = time.split(':')
        result = ((int(d) + 360) + int(m)) * 60 + int(float(s))
        return result
    
    if len(time.split(':')) == 1:
        (h) = time
        result = int(h) * 3600
    
        return result
    if len(time.split(':')) == 2:
        (h, m) = time.split(':')
        result = int(h) * 3600 + int(m)
    
        return result
    
    (h, m, s) = time.split(':')
    
    result = int(h) * 3600 + int(m) * 60 + float(s)
    
    return result


def dms_degree(dms_dec):

    dec = dms_dec.split(":")
    if len(dec) != 3:
        raise ValueError("Value is not in the form degree:minutes:seconds (00:00:00*)")
    if int(dec[1]) > 60 or float(dec[2]) > 60 or int(dec[1]) + (float(dec[2])/60) > 60:
        raise ValueError("Minutes and/or seconds can not be greater than 60")
    return int(dec[0]) + int(dec[1]) / 60 + float(dec[2]) / 3600


def hms_degree(hms_ra):
    ra = hms_ra.split(":")
    if len(ra) != 3:
        raise ValueError("Value of declination is not in the form hours:minutes:seconds (00:00:00*)")

    if int(ra[0]) > 24 or int(ra[1]) > 60 or float(ra[2]) > 60:
        raise ValueError("Hours can not be grater than 24 and/or minutes and/or seconds can not be greater than 60")

    if (int(ra[0]) + int(ra[1]) / 60 + float(ra[2]) / 3600) / (24 / 360) > 360:
        raise ValueError("Maximum hours in a day are 24:00:00 ")

    return (int(ra[0]) + int(ra[1]) / 60 + float(ra[2]) / 3600) / (24 / 360)
