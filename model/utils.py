def to_number(value) -> float: 
    if value is None:
        raise ValueError("Value cannot be None")
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        clean_val = value.strip()
        
        if not clean_val:
            raise ValueError("Invalid number format: {}".format(value))

        try:
            if clean_val.endswith("M"):
                return float(clean_val[:-1])
            elif clean_val.endswith("K"):
                return float(clean_val[:-1]) / 1000
            else:
                return float(clean_val)
        except ValueError:
            raise ValueError("Invalid number format: {}".format(value))

    return float(value)