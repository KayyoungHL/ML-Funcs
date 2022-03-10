FUNCTIONS = {
    "sum"   : lambda x: x.sum,
    "count" : lambda x: x.count,
    "mean"  : lambda x: x.mean,
    "min"   : lambda x: x.min,
    "max"   : lambda x: x.max,
    "std"   : lambda x: x.std,
    "median": lambda x: x.median,
}


def boolean(x):
    if   x.lower() == "true" : return True
    elif x.lower() == "false": return False


def isint(x:str) -> bool:
    if type(x) == str:
        if x.isnumeric(): return True
        else            : return False
    elif type(x) == int:
        return True
    else:
        return False