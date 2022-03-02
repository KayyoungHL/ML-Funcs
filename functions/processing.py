from typing import Optional
from fastapi import Request, Query
import json
import pandas as pd
# import modin.pandas as pd

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


# def split(x):
#     try   : return [i.strip() for i in x.split(",") if i.strip() != ""]
#     except: return False


async def set_transpose(item: Request) -> str:
    df = pd.read_json(await item.json()).set_index("index")
    return df.transpose().reset_index().to_json(orient="records")


async def set_groupby(
    item:       Request,
    by:         str,
    func:       str,
    *,
    axis:       Optional[str] = Query(0,       max_length=50),
    as_index:   Optional[str] = Query("True",  max_length=50), 
    sort:       Optional[str] = Query("True",  max_length=50), 
    group_keys: Optional[str] = Query("True",  max_length=50), 
    observed:   Optional[str] = Query("False", max_length=50), 
    dropna:     Optional[str] = Query("True",  max_length=50)
    # level:      Optional[str] = Query(None,    max_length=50), # MultiIndex 에서 사용하는 것! 
) -> str:
    """pandas.DataFrame.groupby(by).func() 결과를 리턴하는 함수
    ```
    available function = sum, count, mean, min, max, std, median
    by는 반드시 존재하는 컬럼명을 쉼표로 구분해서 입력해야 한다. 1개만 입력할 경우 쉽표 X
    axis = 0(row), 1(columns)
    as_index, sort, group_keys, observed, dropna = bool. true나 false가 입력되어야 한다.

    ※ 추후 level 기능 구현 예정
    ```
    Args:
    ```
    func       (str,     required): should be in [sum, count, mean, min, max, std, median]
    item       (Request, required): JSON
    by         (str,     required): should be string array(column names) divied by ","
    *
    axis       (str,     optional): Default: 0,      0(row), 1(columns)
    as_index   (str,     optional): Default: "True"  ?
    sort       (str,     optional): Default: "True"  ?
    group_keys (str,     optional): Default: "True"  ?
    observed   (str,     optional): Default: "False" ?
    dropna     (str,     optional): Default: "True"  true면 na를 드랍, false면 na를 살려둠
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    axis       = 0       if axis       == "" else axis
    as_index   = "True"  if as_index   == "" else as_index
    sort       = "True"  if sort       == "" else sort
    group_keys = "True"  if group_keys == "" else group_keys
    observed   = "False" if observed   == "" else observed
    dropna     = "True"  if dropna     == "" else dropna

    ## func
    func = func.lower()
    if not func in FUNCTIONS:
        return f'"{func}" is invalid function. "func" should be in {FUNCTIONS}'
    
    df = pd.read_json(await item.json()).set_index("index")

    ## by
    try:
        # if by is None:
        #     return '"by" is a required parameter.'
        by = [i.strip() for i in by.split(",") if i.strip() != ""]
        error_list = [i for i in by if i not in df.columns]
        if error_list:
            return f'"by" should be string array(column names) divied by ","\nlist not in DataFrame columns: {error_list}'
    except:
        return '"by" should be string array(column names) divied by ","'

    ## axis
    try:
        axis = int(axis)
        if axis not in [0, 1]: return '"axis" should be 0, 1. row(0), column(1)'
    except:
        return '"axis" should be 0, 1. row(0), column(1)'
    
    ## level(미구현)
    # If the axis is a MultiIndex (hierarchical), group by a particular level or levels.

    ## as_index
    as_index = boolean(as_index)
    if as_index is None: return '"as_index" should be bool, "true" or "false"'

    ## sort
    sort = boolean(sort)
    if sort is None: return '"sort" should be bool, "true" or "false"'
    
    ## group_keys
    group_keys = boolean(group_keys)
    if group_keys is None: return '"group_keys" should be bool, "true" or "false"'

    ## squeeze(미구현)
    # squeeze will deprecated in future version

    ## observed
    observed = boolean(observed)
    if observed is None: return '"observed" should be bool, "true" or "false"'

    ## dropna
    dropna = boolean(dropna)
    if dropna is None: return '"dropna" should be bool, "true" or "false"'


    # pd.DataFrame.groupby
    df_group = df.groupby(
        by         = by,
        axis       = axis,
        # level      = level,
        as_index   = as_index,
        sort       = sort,
        group_keys = group_keys,
        observed   = observed,
        dropna     = dropna
    )
    
    return FUNCTIONS[func](df_group).reset_index().rename({"index":""}).to_json(orient="records")


async def set_drop(
    item:    Request, 
    labels:  str,
    *,
    axis:    Optional[str] = Query(0,       max_length=50),
    errors:  Optional[str] = Query("raise", max_length=50), # or "ignore"
    # index:   Optional[str] = Query(None,    max_length=50), # if   axis = 0 : index = labels
    # columns: Optional[str] = Query(None,    max_length=50), # elif axis = 1 : columns = labels
    # level:   Optional[str] = Query(None,    max_length=50), # level is for multi-index
    # inplace: Optional[str] = Query(False,   max_length=50), # inplace is not needed this way
) -> str:
    """pandas.DataFrame.drop(labels) 를 리턴하는 함수
    ```
    labels는 반드시 존재하는 컬럼 or 인덱스명을 쉼표로 구분해서 입력해야 한다. 1개만 입력할 경우 쉽표 X
    axis = 0(row), 1(columns)

    ※ 추후 level 구현 예정
    ```
    Args:
    ```
    item   (Request, required): JSON
    labels (str,     required): should be string/int array(index or column names) divied by ","
    *
    axis   (str,     optional): Default: 0,      0(row, index), 1(columns)
    errors (str,     optional): Default: "raise" raise면 없는 것을 drop 시도할 때 에러 발생, ignore면 에러 발생X
    ```
    Returns:
    ```
    str: JSON
    ```
    """

    axis   = 0       if axis   == "" else axis
    errors = "raise" if errors == "" else errors

    ## errors
    errors = errors.lower()
    if errors not in ["raise", "ignore"]:
        return f'"errors" should be "raise" or "ignore". current errors = {errors}'

    df = pd.read_json(await item.json()).set_index("index")

    ## axis
    try:
        axis = int(axis)
        if axis not in [0, 1]: return '"axis" should be 0, 1. row(0), column(1)'
    except:
        return '"axis" should be 0, 1. row(0), column(1)'
    
    #labels
    try:
        # if labels is None:
        #     return '"labels" is a required parameter.'
        labels = [i.strip() for i in labels.split(",") if i.strip() != ""]
        if errors == "raise":
            if axis: 
                dfcols = df.columns
                if str(dfcols.dtype) != "object": labels = [int(i) for i in labels]
                dfcols = set(dfcols)
                error_list = [i for i in labels if i not in dfcols]
            else:
                idxs = df.index
                if str(idxs.dtype) != "object": labels = [int(i) for i in labels]
                idxs = set(idxs)
                error_list = [i for i in labels if i not in idxs]
            if error_list:
                if axis: return f'"labels" should be string array(column names) divied by ","\nlist not in DataFrame columns: {error_list}'
                else   : return f'"labels" should be string array(index names) divied by ","\nlist not in DataFrame indexes: {error_list}'
    except:
        return '"labels" should be string array(column names) divied by ","'
    
    return df.drop(
        labels = labels,
        axis   = axis,
        errors = errors,
        # index=None,
        # columns=None,
        # level=None,
        # inplace=False,
    ).reset_index().to_json(orient="records")


async def set_dropna(
    item:    Request,
    *,
    axis:    Optional[str] = Query(0,       max_length=50),
    how:     Optional[str] = Query('any',   max_length=50), # or 'all'
    thresh:  Optional[str] = Query(None,    max_length=50),
    subset:  Optional[str] = Query(None,    max_length=50),
    # inplace: Optional[str] = Query("false", max_length=50), # inplace is not needed in this way
) -> str:
    """pandas.DataFrame.dropna() 를 리턴하는 함수

    Args:
    ```
    item  (Request, required): JSON
    *
    axis  (str,     optional): Default: 0,     0(row), 1(column)
    how   (str,     optional): Default: 'any', 'any': na 하나라도 있으면 드랍, 'all':전부 na면 드랍
    thresh(str,     optional): Default: None,  thresh 수 이하의 데이터가 있는 컬럼 드랍
    subset(str,     optional): Default: None,  해당 column에서 na인 row를 drop하기 위해 씀
    ```
    Returns:
    ```
    str: JSON
    ```
    """

    axis   = 0     if axis   == "" else axis
    how    = 'any' if how    == "" else how
    thresh = None  if thresh == "" else thresh
    subset = None  if subset == "" else subset

    ## axis
    try:
        axis = int(axis)
        if axis not in [0, 1]: return '"axis" should be 0, 1. row(0), column(1)'
    except:
        return '"axis" should be 0, 1. row(0), column(1)'
    
    ## how
    how = how.lower()
    if how not in ["any", "all"]:
        return f'"how" should be "any" or "all". current how = {how}'

    ## thresh => threshold: 최소 thresh 만큼 데이터가 없으면 드랍
    # int, optional
    # Require that many non-NA values.
    if thresh is not None:
        try:
            thresh = int(thresh)
            if thresh <= 0: return f'"thresh" should be positive integer. current thresh = {thresh}'
        except:
            return f'"thresh" should be positive integer. current thresh = {thresh}'

    df = pd.read_json(await item.json()).set_index("index")

    ## subset => dropna를 하면서 삭제하고 싶은 컬럼을 적으면 된다.
    # column label or sequence of labels, optional
    # Labels along other axis to consider, e.g. if you are dropping rows
    # these would be a list of columns to include.
    if subset is not None:
        try:
            subset = [i.strip() for i in subset.split(",") if i.strip() != ""]
            error_list = [i for i in subset if i not in df.columns]
            if error_list:
                return f'"subset" should be string array(column names) divied by ",". list not in DataFrame columns: {error_list}'
        except:
            return f'"subset" should be string array(column names) divied by ",". current subset = {subset}'

    return df.dropna(
        axis    = axis,
        how     = how,
        thresh  = thresh,
        subset  = subset,
        # inplace = False,
    ).reset_index().to_json(orient="records")


async def set_rename(
    item:    Request,
    # mapper:  str, # it should be dict so it is seperated key and value
    keys:    str,
    values:  str,
    *,
    copy:    Optional[str] = Query("true",   max_length=50),
    errors:  Optional[str] = Query("ignore", max_length=50), # or "raise"
    # axis:    Optional[str] = Query(1,        max_length=50), # It's not needed. We'll only change column names
    # index:   Optional[str] = Query(None,     max_length=50), # if   axis = 0 : index = mapper
    # columns: Optional[str] = Query(None,     max_length=50), # elif axis = 1 : columns = mapper
    # inplace: Optional[str] = Query("false",  max_length=50), # inplace is not needed in this way
    # level:   Optional[str] = Query(None,     max_length=50), # level is for multi-index
) -> str:
    """
    ```python
    pandas.DataFrame.rename() 을 리턴하는 함수
    ```
    Args:
    ```
    item   (Request, required): JSON
    keys   (str,     required): "keys" should be string array(column names) divied by ","
    values (str,     required): "values" should be string array(new column names) divied by ","
    *
    copy   (str,     optional): Default "true",   ??? "Also copy underlying data"
    errors (str,     optional): Default "ignore", "raise" 일 경우 keys에 없는 컬럼명이 있는 경우 에러 발생
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    copy   = "true"   if copy   == "" else copy
    errors = "ignore" if errors == "" else errors

    df = pd.read_json(await item.json()).set_index("index")

    ## keys
    try:
        keys = [i.strip() for i in keys.split(",") if i.strip() != ""]
        if errors == "raise":
            error_list = [i for i in keys if i not in df.columns]
            if error_list:
                return f'"keys" should be string array(column names) divied by ",". list not in DataFrame columns: {error_list}'
    except:
        return f'"keys" should be string array(column names) divied by ",". current keys = {keys}'
    
    ## values
    try:
        values = [i.strip() for i in values.split(",") if i.strip() != ""]
    except:
        return f'"values" should be string array(new column names) divied by ",". current values = {values}'
    
    if len(keys) != len(values):
        return f'"keys" and "values" should be same length. current len(keys) = {len(keys)} != {len(values)} = len(values)'

    ## copy
    copy = boolean(copy)
    if copy is None: return '"copy" should be bool, "true" or "false"'

    ## errors
    errors = errors.lower()
    if errors not in ["raise", "ignore"]:
        return f'"errors" should be "raise" or "ignore". current errors = {errors}'
    
    mapper = {keys[i]:values[i] for i in range(len(keys))}
    
    return df.rename(
        mapper = mapper,
        axis   = 1,
        copy   = copy,
        errors = errors,
    ).reset_index().to_json(orient="records")


async def set_sort_values(
    item:    Request,
    by:      str,
    *,
    axis:    Optional[str] = Query(0,           max_length=50),
    ascd:    Optional[str] = Query("true",      max_length=50),
    kind:    Optional[str] = Query("quicksort", max_length=50),
    na_pos:  Optional[str] = Query("last",      max_length=50),
    ig_idx:  Optional[str] = Query("false",     max_length=50),
    key:     Optional[str] = Query(None,        max_length=50),
    # inplace: Optional[str] = Query("false",     max_length=50), # inplace is not needed in this way
) -> str:
    """
    ```python
    pandas.DataFrame.sort_value(by) #의 결과를 리턴하는 함수
    ```

    Args:
    ```
    item   (Request, required): JSON
    by     (str,     required): "by" should be string array(column names) divied by ","
    *
    axis   (str,     optional): Default 0,           0: row, 1: column
    ascd   (str,     optional): Default "true",      true: 오름차순, false: 내림차순
    kind   (str,     optional): Default "quicksort", 정렬방법 "quicksort", "mergesort", "heapsort", "stable"
    na_pos (str,     optional): Default "last",      정렬시 결측치 위치 "first"는 앞부분 or "last"는 뒷부분 ascd에 영향을 안 받음.
    ig_idx (str,     optional): Default "false",     false면 인덱스 유지, true면 정렬 후 인덱스를 0부터 새로 붙임
    key    (str,     optional): Default None,        키 callable이라 일단 구현 보류

    Returns:
    ```
    str: JSON
    ```
    """
    axis   = 0           if axis   == "" else axis
    ascd   = "true"      if ascd   == "" else ascd
    kind   = "quicksort" if kind   == "" else kind
    na_pos = "last"      if na_pos == "" else na_pos
    ig_idx = "false"     if ig_idx == "" else ig_idx
    key    = None        if key    == "" else key

    df = pd.read_json(await item.json()).set_index("index")

    ## by
    try:
        by = [i.strip() for i in by.split(",") if i.strip() != ""]
        error_list = [i for i in by if i not in df.columns]
        if error_list:
            return f'"by" should be string array(column names) divied by ","\nlist not in DataFrame columns: {error_list}'
    except:
        return '"by" should be string array(column names) divied by ","'
    
    ## axis
    try:
        axis = int(axis)
        if axis not in [0, 1]: return '"axis" should be 0, 1. row(0), column(1)'
    except:
        return '"axis" should be 0, 1. row(0), column(1)'

    ## ascd: ascending
    ascd = boolean(ascd)
    if ascd is None: return '"ascd: ascending" should be bool, "true" or "false"'

    ## kind
    kind = kind.lower()
    if kind not in ["quicksort", "mergesort", "heapsort", "stable"]:
        return f'"kind" should be ["quicksort", "mergesort", "heapsort", "stable"]. current kind = {kind}'

    ## na_pos: na_position
    na_pos = na_pos.lower()
    if na_pos not in ["first", "last"]:
        return f'"na_pos: na_position" should be "first" or "last". current na_pos: na_pos = {na_pos}'    

    ## ig_idx: ignore_index
    ig_idx = boolean(ig_idx)
    if ig_idx is None: return '"ig_idx: ignore_index" should be bool, "true" or "false"'
    
    ## key => sorted 함수의 key와 동일. 함수를 넣어야 해서 일단 구현 보류
    # callable, optional
    # If not None, apply the key function to the series values
    # before sorting. This is similar to the `key` argument in the
    # builtin :meth:`sorted` function, with the notable difference that
    # this `key` function should be *vectorized*. It should expect a
    # ``Series`` and return an array-like.
    
    return df.sort_values(
        by           = by,
        axis         = axis,
        ascending    = ascd,
        kind         = kind,
        na_position  = na_pos,
        ignore_index = ig_idx,
        key          = key, # 현재 미구현
        # inplace      = inplace,
    ).reset_index().to_json(orient="records")


async def set_merge(
    item:        Request, 
    # item2:       Request,
    *,
    how:         Optional[str] = Query("inner",     max_length=50),
    on:          Optional[str] = Query(None,        max_length=50),
    left_on:     Optional[str] = Query(None,        max_length=50),
    right_on:    Optional[str] = Query(None,        max_length=50),
    left_index:  Optional[str] = Query("false",     max_length=50),
    right_index: Optional[str] = Query("false",     max_length=50),
    sort:        Optional[str] = Query("false",     max_length=50),
    # suffixes:    Optional[str] = Query(("_x","_y"), max_length=50),
    left_suf:    Optional[str] = Query("_x",        max_length=50),
    right_suf:   Optional[str] = Query("_y",        max_length=50),
    copy:        Optional[str] = Query("true",      max_length=50),
    indicator:   Optional[str] = Query("false",     max_length=50),
    validate:    Optional[str] = Query(None,        max_length=50),
) -> str:
    """
    ```python
    pandas.DataFrame.merge(pandas.DataFrame) # 의 결과를 리턴하는 함수
    ```
    Args:
    ```
    item        (Request, required): JSON {"left":DataFrame, "right":DataFrame}
    *
    how         (str,     optional): Default "inner", inner: inner join, outer: outer join
    on          (str,     optional): Default None,    조인할 대상 컬럼(양쪽 DataFrame에 다 있어야 함)
    left_on     (str,     optional): Default None,    조인할 대상 컬럼(왼쪽)
    right_on    (str,     optional): Default None,    조인할 대상 컬럼(오른쪽)
    left_index  (str,     optional): Default "false", ??
    right_index (str,     optional): Default "false", ??
    sort        (str,     optional): Default "false", true: 인덱스 기준으로 정렬, false 정렬 안 함
    left_suf    (str,     optional): Default "_x",    왼쪽 dataframe 컬럼에 붙일 접미사(on이 아닐경우)
    right_suf   (str,     optional): Default "_y",    오른쪽 dataframe 컬럼에 붙일 접미사(on이 아닐경우)
    copy        (str,     optional): Default "true",  잘 모르겠음
    indicator   (str,     optional): Default "false", 잘 모르겠음
    validate    (str,     optional): Default None,    머지된 dataframe이 해당 유형인지 확인
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    how         = "inner" if how         == "" else how
    on          = None    if on          == "" else on
    left_on     = None    if left_on     == "" else left_on
    right_on    = None    if right_on    == "" else right_on
    left_index  = "false" if left_index  == "" else left_index
    right_index = "false" if right_index == "" else right_index
    sort        = "false" if sort        == "" else sort
    left_suf    = "_x"    if left_suf    == "" else left_suf
    right_suf   = "_y"    if right_suf   == "" else right_suf
    copy        = "true"  if copy        == "" else copy
    indicator   = "false" if indicator   == "" else indicator
    validate    = None    if validate    == "" else validate

    item = await item.json()
    df_left = pd.read_json(item["left"]).set_index("index")
    df_right = pd.read_json(item["right"]).set_index("index")

    ## how
    if how not in {"left", "right", "outer", "inner", "cross"}:
        return f'"how" should be ["left", "right", "outer", "inner", "cross"]. current how = {how}'

    ## on
    # column or index level name(멀티인덱스일때 인덱스 컬럼의 이름)의 리스트
    # 반드시 양 쪽 데이터 프레임에 전부 들어있어야 한다.
    # 인덱스 컬럼은 테스트 확인하고 추가할 예정
    if on is not None:
        try:
            on = [i.strip() for i in on.split(",") if i.strip() != ""]
            error_list = [i for i in on if i not in df_left.columns]
            if error_list:
                return f'"on" should be string array(column names) divied by ","\nlist not in DataFrame1 columns: {error_list}'
            error_list = [i for i in on if i not in df_right.columns]
            if error_list:
                return f'"on" should be string array(column names) divied by ","\nlist not in DataFrame2 columns: {error_list}'
        except:
            return '"on" should be string array(column names) divied by ","'

    ## left_on
    if left_on is not None:
        try:
            left_on = [i.strip() for i in left_on.split(",") if i.strip() != ""]
            error_list = [i for i in left_on if i not in df_left.columns]
            if error_list:
                return f'"left_on" should be string array(column names) divied by ","\nlist not in DataFrame1 columns: {error_list}'
        except:
            return '"left_on" should be string array(column names) divied by ","'
    
    ## right_on
    if right_on is not None:
        try:
            right_on = [i.strip() for i in right_on.split(",") if i.strip() != ""]
            error_list = [i for i in right_on if i not in df_right.columns]
            if error_list:
                return f'"on" should be string array(column names) divied by ","\nlist not in DataFrame2 columns: {error_list}'
        except:
            return '"right_on" should be string array(column names) divied by ","'
    
    ## left_index
    left_index = boolean(left_index)
    if left_index is None: return '"left_index" should be bool, "true" or "false"' 

    ## right_index
    right_index = boolean(right_index)
    if right_index is None: return '"right_index" should be bool, "true" or "false"' 

    ## sort
    sort = boolean(sort)
    if sort is None: return '"sort" should be bool, "true" or "false"'

    ## suffixes
    suffixes = (left_suf,right_suf)

    ## copy
    copy = boolean(copy)
    if copy is None: return '"copy" should be bool, "true" or "false"'

    ## indicator
    indicator = boolean(indicator)
    if indicator is None: return '"indicator" should be bool, "true" or "false"'

    ## validate
    #  If specified, checks if merge is of specified type.
    #  “one_to_one” or “1:1”: check if merge keys are unique in both left and right datasets.
    #  “one_to_many” or “1:m”: check if merge keys are unique in left dataset.
    #  “many_to_one” or “m:1”: check if merge keys are unique in right dataset.
    #  “many_to_many” or “m:m”: allowed, but does not result in checks.
    if validate is not None:
        if validate not in {"1:1", "1:m", "m:1", "m:m", "one_to_one", "one_to_many", "many_to_one", "many_to_many"}:
            return f'"validate" should be ["1:1", "1:m", "m:1", "m:m", "one_to_one", "one_to_many", "many_to_one", "many_to_many"]. current validate = {validate}'

    return df_left.merge(
        right        = df_right,
        how          = how,
        on           = on,          #: IndexLabel | None = None,
        left_on      = left_on,     #: IndexLabel | None = None,
        right_on     = right_on,    #: IndexLabel | None = None,
        left_index   = left_index,  #: bool = False,
        right_index  = right_index, #: bool = False,
        sort         = sort,        #: bool = False,
        suffixes     = suffixes,    #: Suffixes = ("_x", "_y"),
        copy         = copy,        #: bool = True,
        indicator    = indicator,   #: bool = False,
        validate     = validate,    #: str | None = None,
    ).reset_index().to_json(orient="records")


async def set_concat(
    item:       Request,
    *,
    axis:       Optional[str] = Query(0,       max_length=50),
    join:       Optional[str] = Query("outer", max_length=50),
    ig_idx:     Optional[str] = Query("false", max_length=50),
    keys:       Optional[str] = Query(None,    max_length=50),
    # levels:     Optional[str] = Query(None,    max_length=50),
    names:      Optional[str] = Query(None,    max_length=50),
    veri_integ: Optional[str] = Query("false", max_length=50),
    sort:       Optional[str] = Query("false", max_length=50),
    copy:       Optional[str] = Query("true",  max_length=50),
) -> str:
    """
    ```python
    pd.concat([pandas.DataFrame, pandas.DataFrame]) # 의 결과를 리턴하는 함수
    ```
    Args:
    ```
    item       (Request, required): JSON {"left":DataFrame, "right":DataFrame}
    *
    axis       (str,     optional): Default 0,       row(0), column(1)
    join       (str,     optional): Default "outer", "inner", "outer"
    ig_idx     (str,     optional): Default "false", true: 인덱스를 새로 붙인다. false: 인덱스를 바꾸지 않고 합친다.
    keys       (str,     optional): Default None,    "keys" should be string array(grouped index names) divied by ","
    # levels:    (str,     optional): Default None,    멀티인덱스에 필요한 기능 => 현재 미구현
    names      (str,     optional): Default None,    "names" should be string array(grouped index`s column names) divied by ","
    veri_integ (str,     optional): Default "false", true: axis에 따라 중복된 컬럼 또는 row가 있으면 에러 발생! false: 에러 없음
    sort       (str,     optional): Default "false", true: 인덱스 기준으로 정렬한다 false: 정렬 안 한다
    copy       (str,     optional): Default "true",  
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    axis       = 0       if axis       == "" else axis
    join       = "outer" if join       == "" else join
    ig_idx     = "false" if ig_idx     == "" else ig_idx
    keys       = None    if keys       == "" else keys
    # levels     = None    if levels     == "" else levels
    names      = None    if names      == "" else names
    veri_integ = "false" if veri_integ == "" else veri_integ
    sort       = "false" if sort       == "" else sort
    copy       = "true"  if copy       == "" else copy

    item = await item.json()
    df_left = pd.read_json(item["left"]).set_index("index")
    df_right = pd.read_json(item["right"]).set_index("index")

    if type(df_left) == type(df_right) == pd.DataFrame:
        objs = [df_left, df_right]
    else:
        return "merge must be needed two DataFrame"
    
    ## axis
    try:
        axis = int(axis)
        if axis not in [0, 1]: return '"axis" should be 0, 1. row(0), column(1)'
    except:
        return '"axis" should be 0, 1. row(0), column(1)'
    
    ## join
    if join not in ['inner', 'outer']:
        return f'"join" should be ["inner", "outer"]. current join = {join}'
    
    ## ig_idx
    ig_idx = boolean(ig_idx)
    if ig_idx is None: return '"ig_idx" should be bool, "true" or "false"'

    ## keys
    #  pd.concat([s1, s2], keys=['s1', 's2'])
    #  s1  0    a
    #      1    b
    #  s2  0    c
    #      1    d
    #  dtype: object
    if keys is not None:
        try   : keys = [i.strip() for i in keys.split(",") if i.strip() != ""]
        except: return '"keys" should be string array(grouped index names) divied by ","'

    ## levels
    # 멀티인덱스 사용할 때 필요함. 추후 구현 예정


    ## names
    #  pd.concat([s1, s2], keys=['s1', 's2'], names=['Series name', 'Row ID'])
    #  Series name | Row ID
    #  s1          | 0         a
    #              | 1         b
    #  s2          | 0         c
    #              | 1         d
    #  dtype: object
    if names is not None:
        try   : names = [i.strip() for i in names.split(",") if i.strip() != ""]
        except: return '"names" should be string array(grouped index`s column names) divied by ","'

    ## veri_integ => verify_integrity
    #  Check whether the new concatenated axis contains duplicates. 
    #  This can be very expensive relative to the actual data concatenation.
    veri_integ = boolean(veri_integ)
    if veri_integ is None: return '"veri_integ: verify_integrity" should be bool, "true" or "false"'

    ## sort
    sort = boolean(sort)
    if sort is None: return '"sort" should be bool, "true" or "false"'

    ## copy
    copy = boolean(copy)
    if copy is None: return '"copy" should be bool, "true" or "false"'

    return pd.concat(
        objs             = objs,       #: Iterable[NDFrame] | Mapping[Hashable, NDFrame],
        axis             = axis,       #: Axis = 0,
        join             = join,       #: str = "outer",
        ignore_index     = ig_idx,     #: bool = False,
        keys             = keys,
        # levels           = levels,
        names            = keys,
        verify_integrity = veri_integ, #: bool = False,
        sort             = sort,       #: bool = False,
        copy             = copy,       #: bool = True,
    ).reset_index().to_json(orient="records")


from collections import deque

async def set_column(
    item    : Request,
    col     : str,
    *,
    cols    : Optional[str] = Query(None, max_length=50), # for func
    col_from: Optional[str] = Query(None, max_length=50), # for func
    col_to  : Optional[str] = Query(None, max_length=50), # for func
    func    : Optional[str] = Query(None, max_length=50),
    cols_ops: Optional[str] = Query(None, max_length=50),
) -> str:
    """
    ```
    item은 입력받을 dataframe,
    col은 새로 생성 또는 값을 변경할 컬럼 명.(기존 컬럼에 있으면 기존 컬럼을 변경하고 아니면 새로 생성)

    사용 방법 2가지
    1. cols or col_from:col_to / func
    2. cols_ops

    둘 다 동시에 사용할 수 없음

    
    ※ func 사용시 유의사항
    1. cols 를 사용하면 col_from:col_to 는 사용할 수 없습니다. 둘 중 하나 사용 가능
    2. func는 다음 중 하나여야 합니다. ["sum", "count", "mean", "min", "max", "std", "median"]


    ※ cols_ops 사용시 유의사항
    1. column 명이 숫자일 경우, 컬럼을 연산하라는 것인지 숫자를 연산하라는 것인지 구분이 불가능합니다.
    (키워드 약속하면 구분해서 처리할 수는 있습니다.)
    2. + => %2b 로 파라미터를 보내셔야합니다
    3. 반드시 column 또는 숫자로 시작해서 column 또는 숫자로 끝나야 합니다.
    4. 홀수 자리는 반드시 연산자가 와야 합니다.(^, /, *, -, +)
    ```
    Args:
    ```
    item     (Request, required): JSON
    col      (str,     required): 새로 생성하거나 변경할 컬럼 명
    *
    cols     (str,     optional) = Default: None, 쉼표로 구분된 컬럼명(반드시 df에 포함되어 있어야 함) funt 쓸 때 사용
    col_from (str,     optional) = Default: None, funt 쓸 때 사용
    col_to   (str,     optional) = Default: None, funt 쓸 때 사용
    func     (str,     optional) = Default: None, ["sum", "count", "mean", "min", "max", "std", "median"] 중 하나
    cols_ops (str,     optional) = Default: None, 쉼표로 구분된 컬럼or숫자와 연산자(^, /, *, -, +)
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    cols     = None if cols     == "" else cols
    col_from = None if col_from == "" else col_from
    col_to   = None if col_to   == "" else col_to
    func     = None if func     == "" else func
    cols_ops = None if cols_ops == "" else cols_ops

    df = pd.read_json(await item.json()).set_index("index")
    dfcols = set(df.columns)
    # left: df[col], right: some function
    # df[col] =

    if cols_ops:
        # cols_ops
        operators = {
            "^" : lambda x, y: x ** y,
            "/" : lambda x, y: x / y,
            "*" : lambda x, y: x * y,
            "-" : lambda x, y: x - y,
            "+" : lambda x, y: x + y,
        }

        deq = deque()

        if cols_ops:
            try   : cols_ops = [i.strip() for i in cols_ops.split(",") if i.strip() != ""]
            except: return '"cols_ops" should be array(column names and operators) divied by ","'
            for i, v in enumerate(cols_ops):
                if i%2 == 0:
                    if v in dfcols: deq.append(df[v]) # df columns이면 시리즈로
                    else : 
                        try   : deq.append(float(v))  # 아니면 그냥 numeric으로
                        except: return f'"{v}" is not in columns of DataFrame. It should be in {dfcols}'
                else:
                    deq.append(v)

        for op in operators:    # 모든 연산자에 대해 우선순위 대로
            cols_ops = deq
            deq = deque()
            while len(cols_ops) != 0:
                cur = cols_ops.popleft()
                if type(cur) is str and cur == op:
                    left = deq.pop()
                    right = cols_ops.popleft()
                    cur = operators[cur](left, right)
                deq.append(cur)
        
        df[col] = deq.pop()

    else:
        ## func
        func = func.lower()
        if not func in FUNCTIONS:
            return f'"{func}" is invalid function. "func" should be in {FUNCTIONS}'
        
        # cols = col1,col2,col3....
        # math = + - x /
        # func = sum, std, mean ...
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
                except: return "column type is int. cols should be int."
        else:
            if cols is not None:
                try   : cols = [i.strip() for i in cols.split(",") if i.strip() != ""]
                except: return '"cols" should be array(column names) divied by ","'


        if cols     and not set(cols)<= dfcols: return f'"{cols}" is not in columns of DataFrame. It should be in {dfcols}'
        if col_from and col_from not in dfcols: return f'"{col_from}" is not in columns of DataFrame. It should be in {dfcols}'
        if col_to   and col_to   not in dfcols: return f'"{col_to}" is not in columns of DataFrame. It should be in {dfcols}'



        df_func = df[cols] if cols else df[:,col_from:col_to]
        df[col] = FUNCTIONS[func](df_func)(axis=1)

    return df.reset_index().to_json(orient="records")


async def set_astype(item: Request, col:str, dtype:str) -> str:
    """
    ```python
    pandas.DataFrame[col].astype(dtype) #을 구현한 함수 
    ```
    Args:
    ```
    item (Request, required): JSON
    col  (str    , required): column 명
    dtype(str    , required): ["int", "float", "category", "object", "datetime64[ns]"] 중 하나
    ```
    Returns:
    ```
    str: JSON
    ```
    """
    if dtype not in ["int", "float", "category", "object", "datetime64[ns]"]:
        return f"{dtype}: 올바르지 않은 데이터 타입"
    df = pd.read_json(await item.json()).set_index("index")
    if col not in set(df.columns):
        return f"{col}: 존재하지 않는 컬럼"
    df[col] = df[col].astype(dtype)
    return df.reset_index().to_json(orient="records")