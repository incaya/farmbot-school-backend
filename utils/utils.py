def contains(rstr, vlist):
    res = [v for v in vlist if(v in rstr)] if rstr else None
    return True if res and bool(res) else None
