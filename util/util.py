def handle_missing_header(header_obj, header):
    try:
        return header_obj[header]
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
    
    result = int(h) * 3600 + int(m) * 60 + int(float(s))
    
    return result
