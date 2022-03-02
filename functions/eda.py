from typing import Optional
from fastapi import Request, Query
import json
import numpy as np
import pandas as pd
# import modin.pandas as pd


async def get_head(item: Request, *, line: Optional[str] = Query(5, max_length=50)) -> str:
    try:    line = int(line)
    except: line = 5
    return pd.read_json(await item.json()).head(line).to_json(orient="records")


async def get_tail(item: Request, *, line: Optional[str] = Query(5, max_length=50)) -> str:
    try:    line = int(line)
    except: line = 5
    return pd.read_json(await item.json()).tail(int(line)).to_json(orient="records")


async def get_shape(item: Request) -> str:
    df = pd.read_json(await item.json()).set_index("index")
    return json.dumps(df.shape)


async def get_dtype(item: Request) -> str:
    return pd.read_json(await item.json()).set_index("index").dtypes.reset_index(name='Dtype').rename(columns={"index":"Column"}).to_json(orient="records", default_handler=str)


async def get_columns(item: Request) -> str:
    df = pd.read_json(await item.json()).set_index("index")
    return f"{list(df.columns)}"


# async def get_unique(item: Request) -> str:
#     """입력이 Series의 JSON일 경우"""
#     try:
#         return f"{list(pd.read_json(await item.json()).unique())}"
#     except:
#         return "input JSON should be converted to pandas.Series"


async def get_unique(item: Request, col: str) -> str:
    """입력이 DataFrame의 JSON일 경우

    /file/unique/컬럼명 에서 컬럼명이 DataFrame에 없을 경우 에러메시지를 리턴한다."""
    df = pd.read_json(await item.json()).set_index("index")
    try:
        if col not in df.columns:
            return f"{col} is not in columns of DataFrame. It should be in {list(df.columns)}"
        return f"{list(df[col].unique())}"
    except:
        return "input JSON should be converted to pandas.DataFrame"


async def get_na(item: Request, *, sum: Optional[str] = Query("false", max_length=50)) -> str:
    """결측치 확인 함수
    `/file/isna`
    `/file/isna?sum=true`

    Args:
    ```
    item (Request) : JSON, 사용할 때 `await item.json()`
    sum  (optional): default = "false"
                     "true" 일 경우 결측치의 합을 포함한 시리즈를 리턴
    ```
    Returns:
    ```
    (str): JSON
    ```
    """
    df = pd.read_json(await item.json()).set_index("index")
    if   sum.lower() == "true" : 
        return df.isna().sum().reset_index(name='NumOfNaN')\
            .rename(columns={"index":"Column"}).to_json(orient="records", default_handler=str)
    elif sum.lower() == "false": return df.isna().to_json(orient="records")
    else                       : return "sum은 true or false를 넣으셔야 합니다."


async def get_corr(
    item   : Request,
    *,
    method : Optional[str] = Query("pearson", max_length=50),
    req_min: Optional[str] = Query(1, max_length=50),
    col1   : Optional[str] = Query(None, max_length=50),
    col2   : Optional[str] = Query(None, max_length=50),
) -> str:
    """상관관계를 반환해주는 함수
    ```
    req_min은 상관관계를 구하기 위해 필요한 최소한의 데이터 수를 의미합니다.
    만약 na 값이 많아서 유의미한 데이터를 구하기 어려운 경우 req_min을 통해 해당 columns에서 구한 상관관계 값을 NaN으로 바꿀 수 있습니다.

    col1, col2는 데이터가 클 때, 보고 싶은 데이터만 볼수 있는 기능입니다.
    col1, col2 둘 다 입력: 두 columns의 상관관계만 리턴
    col1, col2 둘 중 하나: 해당 column과 나머지의 상관관계를 리턴

    인덱스를 살려야 함.
    ```
    Args:
    ```
    item   (Request, required): JSON
    method     (str, optional): Default "pearson", 상관관계 방식. 셋 중 하나 ["pearson", "kendall", "spearman"]
    req_min    (str, optional): Default 1,         상관관계 계산에 필요한 최소 데이터 수. 양의 정수
    col1       (str, optional): Default None,      columns명, DataFrame에 없으면 에러 반환
    col2       (str, optional): Default None,      columns명, DataFrame에 없으면 에러 반환
    ```
    Returns:
    ```
    (str): JSON
    ```
    """
    method  = "pearson" if method  == "" else method
    req_min = 1         if req_min == "" else req_min
    col1    = None      if col1    == "" else col1
    col2    = None      if col2    == "" else col2

    if not method in ["pearson", "kendall", "spearman"]:
        return 'method should be in ["pearson", "kendall", "spearman"]'
    
    try   : 
        req_min = int(req_min)
        if req_min <= 0:
            raise Exception
    except: 
        return "req_min should be positive integer"
    
    df = pd.read_json(await item.json()).set_index("index")
    dfcols = list(df.columns)
    if col1 and col1 not in dfcols: return f"{col1} is not in columns of DataFrame. It should be in {dfcols}"
    if col2 and col2 not in dfcols: return f"{col2} is not in columns of DataFrame. It should be in {dfcols}"
    
    if col1 and col2:
        return df[col1].corr(
            other       = df[col2],
            method      = method, 
            min_periods = req_min
        )
    elif col1:
        return df.corr(
            method      = method, 
            min_periods = req_min
        )[col1].reset_index(name=col1).rename(columns={"index":"Column"}).to_json(orient="records", default_handler=str)
    elif col2:
        return df.corr(
            method      = method, 
            min_periods = req_min
        )[col2].reset_index(name=col2).rename(columns={"index":"Column"}).to_json(orient="records", default_handler=str)
    else:
        return df.corr(
            method      = method, 
            min_periods = req_min
        ).reset_index().rename(columns={"index":""}).to_json(orient="records")


async def get_describe(
    item:        Request,
    *,
    percentiles: Optional[str] = Query(None, max_length=50),
    num:         Optional[str] = Query(0,    max_length=50),
    obj:         Optional[str] = Query(0,    max_length=50),
    cat:         Optional[str] = Query(0,    max_length=50),
    date:        Optional[str] = Query(0,    max_length=50),
    date2num:    Optional[str] = Query("",   max_length=50)
) -> str:
    """pandas.DataFrame.describe() 결과를 리턴하는 함수
    ```
    percentiles는 보고 싶은 퍼센트의 값을 볼 수 있는 파라미터입니다.
    default로 min, 25%, 50%, 75%, max의 데이터를 반환하는데, 이 옵션을 주면
    다른 min, 50%, max에 추가로 다른 퍼센트의 데이터를 볼 수 있습니다.

    입력은 소수(float)의 배열인데, 쉽표로 구분해주시면 됩니다. 
    ex) min, 10%, 30%, 50% 70% max를 보려면 => .1,.3,.7

    num, obj, cat, date는 해당 자료형을 볼지 안 볼지 결정하는 파라미터입니다.
    default는 0으로 조작을 하지 않는 것입니다.
    넷 전부 0일 경우 default로 numeric 데이터만 보여줍니다.

    1 :해당 자료형의 describe(넷 중 1인 데이터만 보여줍니다.)
    -1:해당 자료형을 제외한 나머지의 describe(넷 중 -1이 아닌 데이터만 보여줍니다.)

    date2num은 true일 경우 datetime 자료형을 numeric 자료형으로 바꿔줍니다.
    ```
    Args:
    ```
    item       (Request, required): JSON
    percentiles(str,     optional): Default None, 해당 퍼센트의 데이터 값을 확인, 쉼표로 구분한 float array: ex) 0.1,0.2,0.4,0.8
    num        (str,     optional): Default 0,    numeric 데이터, -1, 0, 1 중 하나
    obj        (str,     optional): Default 0,    object 데이터, -1, 0, 1 중 하나
    cat        (str,     optional): Default 0,    category 데이터, -1, 0, 1 중 하나
    date       (str,     optional): Default 0,    datetime 데이터, -1, 0, 1 중 하나
    date2num   (str,     optional): Default "",   datetime 데이터를 numeric 데이터로 변환, ture(대소구분X)만 바뀜.
    ```
    Returns:
    ```
    (str): JSON
    ```
    """
    percentiles = None if percentiles == "" else percentiles
    num         = 0    if num         == "" else num
    obj         = 0    if obj         == "" else obj
    cat         = 0    if cat         == "" else cat
    date        = 0    if date        == "" else date
    date2num    = ""   if date2num    == "" else date2num


    if percentiles is not None:
        try:
            percentiles = [float(i) for i in percentiles.split(",") if i.strip() != ""] 
            for i, f in enumerate(percentiles):
                if 100 > f >= 1:
                    percentiles[i] = f/100
                elif not (1 > f > 0):
                    return "percentiles should be 0~1 float string divided by ','"
        except: return "percentiles should be 0~1 float string divided by ','"

    try:
        num = int(num)
        if num not in [-1, 0, 1]:
            return "num should be -1, 0, 1"
    except: return "num should be -1, 0, 1"

    try:    
        obj = int(obj)
        if obj not in [-1, 0, 1]:
            return "obj should be -1, 0, 1"
    except: return "obj should be -1, 0, 1"

    try:
        cat = int(cat)
        if cat not in [-1, 0, 1]:
            return "cat should be -1, 0, 1"
    except: return "cat should be -1, 0, 1"

    try:
        date = int(date)
        if date not in [-1, 0, 1]:
            return "date should be -1, 0, 1"
    except: return "date should be -1, 0, 1"
    """
    Pandas data type
    "int64"      # np.number
    "float64"    # np.number
    "object"     # object, "O"
    "category"   # "category"
    "datetime64" # np.datetime64
    
    Not use
    "timedelta"  #
    "bool"       # 
    """

    df = pd.read_json(await item.json()).set_index("index")
    chk = {str(i) for i in df.dtypes.unique()}
    
    include = []
    exclude = []

    if num:
        if num > 0 : include.append(np.number)     if "int64" in chk or "float64" in chk else ...
        else       : exclude.append(np.number)
    if obj:
        if obj > 0 : include.append(object)        if "object" in chk else ...
        else       : exclude.append(object)
    if cat:
        if cat > 0 : include.append("category")    if "category" in chk else ...
        else       : exclude.append("category")
    if date:
        if date > 0: include.append(np.datetime64) if "datetime64[ns]" in chk else ...
        else       : exclude.append(np.datetime64)
    if len(include) == 3:
        include = "all"
    if len(exclude) == 3:
        exclude = None

    return df.describe(
        percentiles         = percentiles,
        include             = include if include else None,
        exclude             = exclude if exclude else None,
        datetime_is_numeric = True if date2num.lower() == "true" else False
    ).reset_index().rename(columns={"index":"Info"}).to_json(orient="records")


async def get_col_condition(
    item     : Request,
    col      : str,
    *,
    cond1    : Optional[str] = Query(None, max_length=50),
    value1   : Optional[str] = Query(None, max_length=50),
    cond2    : Optional[str] = Query(None, max_length=50),
    value2   : Optional[str] = Query(None, max_length=50),
) -> str:
    """
    ```python
    df = pandas.DataFrame()
    # cond1만 있을 경우  "eq", "gr", "gr_eq", "le", "le_eq"
    df[df[col] == value1] # cond1 = "eq"
    df[df[col] >= value1] # cond1 = "gr_eq"
    df[df[col] >  value1] # cond1 = "gr"
    df[df[col] <= value1] # cond1 = "le_eq"
    df[df[col] <  value1] # cond1 = "le"

    # cond1 & cond2 같이 쓸 경우 내부적으로 cond1은 greater than을 가져가고 cond2는 less than를 가져간다.
    # 사용자는 cond1과 cond2의 방향만 다르게 입력하면 된다.
    
    if value1 >= value2:
        df[(df[col] > value1)|(df[col] < value2)]
    else:
        df[(df[col] > value1)&(df[col] < value2)]
    
    # cond2만 사용할 경우 에러를 반환한다.
    # 둘 다 사용할 때 cond1에 eq가 들어가면 에러를 반환한다.
    ```
    Args:
    ```
    item   (Request, required): JSON
    col    (str,     required): column name
    *
    cond1  (str,     optional): Default None, 조건1. "eq", "gr", "gr_eq", "le", "le_eq"
    value1 (str,     optional): Default None, 조건1에 대한 값 ex) df.col < value1
    cond2  (str,     optional): Default None, 조건2. "gr", "gr_eq", "le", "le_eq"; 조건1이 None이면 에러 발생 
    value2 (str,     optional): Default None, 조건2에 대한 값 ex) (df.col < value1) | (df.col > value2)
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    cond1  = None if cond1  == "" else cond1
    value1 = None if value1 == "" else value1
    cond2  = None if cond2  == "" else cond2
    value2 = None if value2 == "" else value2

    df = pd.read_json(await item.json()).set_index("index")
    
    if cond1 not in ["eq", "gr", "gr_eq", "le", "le_eq"]:
        return f'"cond1" should be in ["eq", "gr", "gr_eq", "le", "le_eq"], current {cond1}'
    if cond2 and cond2 not in ["gr", "gr_eq", "le", "le_eq"]:
        return f'"cond2" should be in ["gr", "gr_eq", "le", "le_eq"], current {cond2}'
    if cond1 and cond2 and (cond1[0] == cond2[0] or cond1[0] == "e"):
        return '"cond1" and "cond2" should be different condition(gr and le)'

    if str(df.columns.dtype) == "int64":
        col = int(col)

    if value1 is not None: 
        if cond1 is None: return '"cond1" should be used.'
        try   : value1 = float(value1)
        except: return '"value1" should be numeric(int or float).'
    else:
        return '"value1" should be used.'
        

    if value2 is not None: 
        if cond2 is None: return 'If use "value2", "cond2" should be used.'
        try   : value2 = float(value2)
        except: return '"value2" should be numeric(int or float).'
        
    
    dfcols = list(df.columns)
    if col in dfcols:
        if cond2:
            if cond1 is None: return '"cond2" needs "cond1". Should not be used alone.'
            if cond1[0] == "l":
                cond2, cond1 = cond1, cond2
                value2, value1 = value1, value2
            if   cond1 == "gr"    and cond2 == "le"   : 
                if value1 >= value2: df = df[(df[col] >  value1)|(df[col] <  value2)]
                else               : df = df[(df[col] >  value1)&(df[col] <  value2)]
            elif cond1 == "gr"    and cond2 == "le_eq":
                if value1 >= value2: df = df[(df[col] >  value1)|(df[col] <= value2)]
                else               : df = df[(df[col] >  value1)&(df[col] <= value2)]
            elif cond1 == "gr_eq" and cond2 == "le"   : 
                if value1 >= value2: df = df[(df[col] >= value1)|(df[col] <  value2)]
                else               : df = df[(df[col] >= value1)&(df[col] <  value2)]
            elif cond1 == "gr_eq" and cond2 == "le_eq": 
                if value1 >= value2: df = df[(df[col] >= value1)|(df[col] <= value2)]
                else               : df = df[(df[col] >= value1)&(df[col] <= value2)]
        elif cond1:
            if   cond1 == "eq"   : df = df[df[col] == value1]
            elif cond1 == "gr"   : df = df[df[col] >  value1]
            elif cond1 == "gr_eq": df = df[df[col] >= value1]
            elif cond1 == "le"   : df = df[df[col] <  value1]
            elif cond1 == "le_eq": df = df[df[col] <= value1]
        
        # print(df)
        return df.reset_index().to_json(orient="records")
    else:
        return f"{col} is not in columns of DataFrame. It should be in {dfcols}"


async def get_loc(
    item     : Request,
    *,
    idx      : Optional[str] = Query(None, max_length=50),
    idx_from : Optional[str] = Query(None, max_length=50),
    idx_to   : Optional[str] = Query(None, max_length=50),
    cols     : Optional[str] = Query(None, max_length=50),
    col_from : Optional[str] = Query(None, max_length=50),
    col_to   : Optional[str] = Query(None, max_length=50),
) -> str:
    """
    ```python
    df = pandas.DataFrame()
    if   idx  is None and cols is None: df.loc[idx_from:idx_to, col_from:col_to]
    elif idx  is None                 : df.loc[idx_from:idx_to, cols]
    elif cols is None                 : df.loc[idx, col_from:col_to]
    else                              : df.loc[idx, cols]
    ```
    Args:
    ```
    item     (Request, required): JSON
    *
    idx      (str,     optional): Default: None, 인덱스 명
    idx_from (str,     optional): Default: None, 시작 인덱스 명
    idx_to   (str,     optional): Default: None, 끝 인덱스 명
    cols     (str,     optional): Default: None, 컬럼 명
    col_from (str,     optional): Default: None, 시작 컬럼 명
    col_to   (str,     optional): Default: None, 끝 컬럼 명
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    idx       = None if idx      == "" else idx
    idx_from  = None if idx_from == "" else idx_from
    idx_to    = None if idx_to   == "" else idx_to
    cols      = None if cols     == "" else cols
    col_from  = None if col_from == "" else col_from
    col_to    = None if col_to   == "" else col_to

    df = pd.read_json(await item.json()).set_index("index")

    if str(df.index.dtype) == "int64":
        if idx is None: 
            if idx_from is not None: 
                try   : idx_from = int(idx_from)
                except: return "index type is int. idx_from should be int."
            if idx_to is not None: 
                try   : idx_to = int(idx_to)
                except: return "index type is int. idx_to should be int."
        else:
            idx_from = idx_to = None
            try   : idx = [int(i) for i in idx.split(",") if i.strip() != ""]
            except: return "index type is int. idx should be int."
    else:
        if idx is not None:
            idx = [i.strip() for i in idx.split(",") if i.strip() != ""]
    
    if str(df.columns.dtype) == "int64":
        if cols is None:
            if col_from is not None: 
                try   : col_from = int(col_from)
                except: return "column type is int. col_from should be int."
            if col_to is not None: 
                try   : col_to = int(col_to)
                except: return "column type is int. col_to should be int."
        else:
            col_from = col_to = None
            try   : cols = [int(i) for i in cols.split(",") if i.strip() != ""]
            except: return "column type is int. cols should be int array divided by ','."
    else:
        if cols is not None:
            try   : cols = [i.strip() for i in cols.split(",") if i.strip() != ""]
            except: return '"cols" should be array(column names) divied by ","'


    idxs = set(df.index)
    if idx      and not set(idx) <= idxs: return f'"{idx}" is not in index of DataFrame. It should be in {idxs}'
    if idx_from and idx_from not in idxs: return f'"{idx_from}" is not in index of DataFrame. It should be in {idxs}'
    if idx_to   and idx_to   not in idxs: return f'"{idx_to}" is not in index of DataFrame. It should be in {idxs}'
    
    dfcols = set(df.columns)
    if cols     and not set(cols)<= dfcols: return f'"{cols}" is not in columns of DataFrame. It should be in {dfcols}'
    if col_from and col_from not in dfcols: return f'"{col_from}" is not in columns of DataFrame. It should be in {dfcols}'
    if col_to   and col_to   not in dfcols: return f'"{col_to}" is not in columns of DataFrame. It should be in {dfcols}'

    if   idx  is None and cols is None: df = df.loc[idx_from:idx_to, col_from:col_to]
    elif idx  is None                 : df = df.loc[idx_from:idx_to, cols]
    elif cols is None                 : df = df.loc[idx, col_from:col_to]
    else                              : df = df.loc[idx, cols]
    
    # print(df)
    return df.reset_index().to_json(orient="records")


async def get_iloc(
    item     : Request,
    *,
    idx      : Optional[str] = Query(None, max_length=50),
    idx_from : Optional[str] = Query(None, max_length=50),
    idx_to   : Optional[str] = Query(None, max_length=50),
    cols     : Optional[str] = Query(None, max_length=50),
    col_from : Optional[str] = Query(None, max_length=50),
    col_to   : Optional[str] = Query(None, max_length=50),
) -> str:
    """
    ```python
    df = pandas.DataFrame()
    if   idx  is None and cols is None: df.iloc[idx_from:idx_to, col_from:col_to]
    elif idx  is None                 : df.iloc[idx_from:idx_to, col]
    elif cols is None                 : df.iloc[idx, col_from:col_to]
    else                              : df.iloc[idx, col]
    ```
    Args:
    ```
    item     (Request, required): JSON
    *
    idx      (str,     optional): Default: None, 인덱스 숫자
    idx_from (str,     optional): Default: None, 시작 인덱스 숫자
    idx_to   (str,     optional): Default: None, 끝 인덱스 숫자+1
    cols     (str,     optional): Default: None, 컬럼 숫자
    col_from (str,     optional): Default: None, 시작 컬럼 숫자
    col_to   (str,     optional): Default: None, 끝 컬럼 숫자+1
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    idx       = None if idx      == "" else idx
    idx_from  = None if idx_from == "" else idx_from
    idx_to    = None if idx_to   == "" else idx_to
    cols      = None if cols     == "" else cols
    col_from  = None if col_from == "" else col_from
    col_to    = None if col_to   == "" else col_to
    
    df = pd.read_json(await item.json()).set_index("index")

    if idx is None: 
        if idx_from is not None: 
            try   : idx_from = int(idx_from)
            except: return "idx_from should be int in iloc."
        if idx_to is not None: 
            try   : idx_to = int(idx_to)
            except: return "idx_to should be int in iloc."
    else:
        idx_from = idx_to = None
        try   : idx = [int(i) for i in idx.split(",") if i.strip() != ""]
        except: return "idx should be int in iloc."

    if cols is None:
        if col_from is not None: 
            try   : col_from = int(col_from)
            except: return "col_from should be int in iloc."
        if col_to is not None: 
            try   : col_to = int(col_to)
            except: return "col_to should be int in iloc."
    else:
        col_from = col_to = None
        try   : cols = [int(i) for i in cols.split(",") if i.strip() != ""]
        except: return "cols should be int in iloc."

    idxs = set(range(len(df.index)))
    if idx      and not set(idx) <= idxs: return f'"{idx}" is not in index of DataFrame. It should be in {idxs}'
    if idx_from and idx_from not in idxs: return f'"{idx_from}" is not in index of DataFrame. It should be in {idxs}'
    if idx_to   and idx_to   not in idxs: return f'"{idx_to}" is not in index of DataFrame. It should be in {idxs}'

    dfcols = set(range(len(df.columns)))
    if cols     and not set(cols)<= dfcols: return f'"{cols}" is not in columns of DataFrame. It should be in {dfcols}'
    if col_from and col_from not in dfcols: return f'"{col_from}" is not in columns of DataFrame. It should be in {dfcols}'
    if col_to   and col_to   not in dfcols: return f'"{col_to}" is not in columns of DataFrame. It should be in {dfcols}'

    if   idx  is None and cols is None: df = df.iloc[idx_from:idx_to, col_from:col_to]
    elif idx  is None                 : df = df.iloc[idx_from:idx_to, cols]
    elif cols is None                 : df = df.iloc[idx, col_from:col_to]
    else                              : df = df.iloc[idx, cols]
    
    # print(df)
    return df.reset_index().to_json(orient="records")
