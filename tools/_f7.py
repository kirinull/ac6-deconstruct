def fmtnum(v):
    if isinstance(v,float):
        return ('%.4f'%v).rstrip('0').rstrip('.') if abs(v)<1e6 else '%.1f'%v
    return str(v)
