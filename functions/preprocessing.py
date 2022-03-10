from typing import Optional
from fastapi import Request, Query
import json
import numpy as np
import pandas as pd
# import modin.pandas as pd
from sklearn.model_selection import train_test_split
# from category_encoders import OneHotEncoder, OrdinalEncoder, TargetEncoder

from .internal_func import (
    FUNCTIONS,
    boolean,
    isint,
)

async def set_feature_target_split(
    item : Request,
    cols : str
) -> str:
    """
    ```python
    # 타겟과 피쳐를 나누는 함수
    target = pandas.DataFrame[cols]               # y
    feature = pandas.DataFrame.drop(cols, axis=1) # X
    ```
    Args:
    ```
    item (Request, required): JSON, 입력 데이터 프레임(전처리 끝난 데이터 프레임)
    cols (str,     required): 쉼표로 구분된 타겟 컬럼.(1개 이상)
    ```
    Returns:
    ```
    str: JSON, {"X":feature_df, "y":target_df}
    ```
    """
    df = pd.read_json(await item.json()).set_index("idx")

    dfcols = set(df.columns)
    try:    cols = [i.strip() for i in cols.split(",") if i.strip() != ""]
    except: return f"올바르지 않은 입력: {cols}"
    if not set(cols) <= dfcols: return f'"{cols}" is not in columns of DataFrame. It should be in {dfcols}'

    y = df[cols]
    X = df.drop(cols, axis=1)

    return json.dumps( {
        "X": X.reset_index().to_json(orient="records"),
        "y": y.reset_index().to_json(orient="records"),
    } )


async def set_train_test_split(
    item        : Request,
    *,
    test_size   : Optional[str] = Query(None,    max_length=50),
    random_state: Optional[str] = Query(None,    max_length=50),
    shuffle     : Optional[str] = Query("true",  max_length=50),
    stratify    : Optional[str] = Query("false", max_length=50),
    valid       : Optional[str] = Query("false", max_length=50),
    valid_size  : Optional[str] = Query(None,    max_length=50),
) -> str:
    """
    ```python
    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y)
    
    # 입력 item은 X 와 y 키에 각각 데이터 프레임이 들어있어야 함.
    # test_size와 train_size는 둘 중 하나만 입력 가능.
    # stratify는 None 또는 'y'만 가능
    ```
    Args:
    ```
    item         (Request, required): JSON, {"X":X_dataframe, "y":y_dataframe}
    *,
    test_size    (str,     optional): Default = None,    0~1 사이의 소수. 테스트 셋의 비율
    random_state (str,     optional): Default = None,    아무 정수. 랜덤 시드
    shuffle      (str,     optional): Default = "true",  셔플 여부. true 셔플함, false, 셔플 안함
    stratify     (str,     optional): Default = "false", 타겟을 지정. train, valid split할 때 true를 입력하면 됨.
    valid        (str,     optional): Default = "false", train, valid, test를 나눌때 true로 
    valid_size   (str,     optional): Default = None,    valid 비율
    ```
    Returns:
    ```
    str: JSON, 
    {
        "X_train": X_train.to_json(orient="records"),
        "X_test" : X_test .to_json(orient="records"),
        "y_train": y_train.to_json(orient="records"),
        "y_test" : y_test .to_json(orient="records"),
    }
    or 
    {
        "X_train": X_train.to_json(orient="records"),
        "X_valid": X_valid.to_json(orient="records"),
        "X_test" : X_test .to_json(orient="records"),
        "y_train": y_train.to_json(orient="records"),
        "y_valid": y_valid.to_json(orient="records"),
        "y_test" : y_test .to_json(orient="records"),
        }
    ```
    """
    test_size    = None    if test_size    == "" else test_size
    random_state = None    if random_state == "" else random_state
    shuffle      = "true"  if shuffle      == "" else shuffle
    stratify     = "false" if stratify     == "" else stratify
    valid        = "false" if valid        == "" else valid
    valid_size   = None    if valid_size   == "" else valid_size

    dfs = await item.json()
    X = pd.read_json(dfs["X"]).set_index("idx")
    y = pd.read_json(dfs["y"]).set_index("idx")

    ## test_size:    0 < test_size < 1 인 float
    if test_size is not None:
        try: 
            test_size = float(test_size)
            if test_size <= 0 or test_size >= 1:
                return f'"test_size" should be float between 0, 1(not equal). current {test_size}'
        except: return f'"test_size" should be float between 0, 1(not equal). current {test_size}'

    # ## train_size:   0 < train_size < 1 인 float
    # if train_size is not None:
    #     if test_size is None:
    #         try: 
    #             train_size = float(train_size)
    #             if train_size <= 0 or train_size >= 1:
    #                 return f'"train_size" should be float between 0, 1(not equal). current {train_size}'
    #         except: return f'"train_size" should be float between 0, 1(not equal). current {train_size}'
    #     else:
    #         return "Can only use train_size when test_size is None"

    ## random_state: 랜덤 시드. int
    try: random_state = int(random_state)
    except: '"random_state" should be int.'

    ## shuffle:      bool 셔플 여부
    shuffle = boolean(shuffle)
    if shuffle is None: return '"shuffle" should be bool, "true" or "false"'

    ## stratify:     특정 값의 비율을 맞춰서 나눈다.
        # stratify : array-like, default=None
        # If not None, data is split in a stratified fashion, using this as
        # the class labels.
        # Read more in the :ref:`User Guide <stratification>`.
    stratify = boolean(stratify)
    if stratify is None: return '"stratify" should be bool, "true" or "false"'


    valid = boolean(valid)
    if valid is None: return '"valid" should be bool, "true" or "false"'

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, # *arrays
        test_size    = test_size,
        random_state = random_state,
        shuffle      = shuffle,
        stratify     = y if stratify else None,
    )
    if valid:
        ## valid_size:    0 < valid_size < 1 인 float
        if valid_size is not None:
            try: 
                valid_size = float(valid_size)
                if valid_size <= 0 or valid_size >= 1:
                    return f'"valid_size" should be float between 0, 1(not equal). current {valid_size}'
            except: return f'"valid_size" should be float between 0, 1(not equal). current {valid_size}'
        valid_size = valid_size/(1-test_size)
        if test_size + valid_size >= 1:
            return '"test_size" + "valid_size" should be less than 1'
        X_train, X_valid, y_train, y_valid = train_test_split(
            X_train, y_train, # *arrays
            test_size    = valid_size,
            random_state = random_state,
            shuffle      = shuffle,
            stratify     = y_train if stratify else None,
        )
        return json.dumps( {
            "X_train": X_train.reset_index().to_json(orient="records"),
            "X_valid": X_valid.reset_index().to_json(orient="records"),
            "X_test" : X_test .reset_index().to_json(orient="records"),
            "y_train": y_train.reset_index().to_json(orient="records"),
            "y_valid": y_valid.reset_index().to_json(orient="records"),
            "y_test" : y_test .reset_index().to_json(orient="records"),
        } )

    # 시계열 기준일 경우 
    # shuffle  = False,
    # stratify = None

    return json.dumps( {
        "X_train": X_train.reset_index().to_json(orient="records"),
        "X_test" : X_test .reset_index().to_json(orient="records"),
        "y_train": y_train.reset_index().to_json(orient="records"),
        "y_test" : y_test .reset_index().to_json(orient="records"),
    } )


# async def set_one_hot_encoder(
#     item          : Request,
#     *,
#     verbose       : Optional[str] = Query(0,       max_length=50),
#     cols          : Optional[str] = Query(None,    max_length=50),
#     drop_invariant: Optional[str] = Query(False,   max_length=50),
#     return_df     : Optional[str] = Query(True,    max_length=50),
#     handle_missing: Optional[str] = Query('value', max_length=50),
#     handle_unknown: Optional[str] = Query('value', max_length=50),
#     use_cat_names : Optional[str] = Query(False,   max_length=50),
# ) -> str:
#     dfs = [pd.read_json(i) for i in json.loads(await item.json())]

#     onehot = OneHotEncoder(
#         verbose=0, 
#         cols=None, 
#         drop_invariant=False, 
#         return_df=True,
#         handle_missing='value', 
#         handle_unknown='value', 
#         use_cat_names=False
#     )
#     df_encoded = []
#     df_encoded.append(onehot.fit_transform(dfs[0]))
#     for i in dfs[1:]:
#         df_encoded.append(onehot.transform(i))
    

# async def set_ordinal_encoder(
#     item          : Request,
#     *,
#     verbose       : Optional[str] = Query(0,       max_length=50),
#     mapping       : Optional[str] = Query(None,    max_length=50),
#     cols          : Optional[str] = Query(None,    max_length=50),
#     drop_invariant: Optional[str] = Query(False,   max_length=50),
#     return_df     : Optional[str] = Query(True,    max_length=50),
#     handle_unknown: Optional[str] = Query('value', max_length=50),
#     handle_missing: Optional[str] = Query('value', max_length=50),
# ) -> str:
#     """_summary_

#     Args:
#         item (Request): _description_
#         *
#         verbose (Optional[str], optional): _description_. Defaults to Query(0,       max_length=50).
#         mapping (Optional[str], optional): _description_. Defaults to Query(None,    max_length=50).
#         cols (Optional[str], optional): _description_. Defaults to Query(None,    max_length=50).
#         drop_invariant (Optional[str], optional): _description_. Defaults to Query(False,   max_length=50).
#         return_df (Optional[str], optional): _description_. Defaults to Query(True,    max_length=50).
#         handle_unknown (Optional[str], optional): _description_. Defaults to Query('value', max_length=50).
#         handle_missing (Optional[str], optional): _description_. Defaults to Query('value', max_length=50).

#     Returns:
#         str: _description_
#     """
#     dfs = [pd.read_json(i) for i in json.loads(await item.json())]

#     ordinal = OrdinalEncoder(
#         verbose=0, 
#         mapping=None, 
#         cols=None, 
#         drop_invariant=False, 
#         return_df=True,
#         handle_unknown='value', 
#         handle_missing='value'
#     )

#     df_encoded = []
#     df_encoded.append(ordinal.fit_transform(dfs[0]))
#     for i in dfs[1:]:
#         df_encoded.append(ordinal.transform(i))
    


# async def set_target_encoder(
#     item            : Request,
#     *,
#     verbose         : Optional[str] = Query(0,       max_length=50),
#     cols            : Optional[str] = Query(None,    max_length=50),
#     drop_invariant  : Optional[str] = Query(False,   max_length=50),
#     return_df       : Optional[str] = Query(True,    max_length=50),
#     handle_missing  : Optional[str] = Query('value', max_length=50),
#     handle_unknown  : Optional[str] = Query('value', max_length=50),
#     min_samples_leaf: Optional[str] = Query(1,       max_length=50),
#     smoothing       : Optional[str] = Query(1.0,     max_length=50),
# ) -> str:
#     dfs = [pd.read_json(i) for i in json.loads(await item.json())]

#     target = TargetEncoder(
#         verbose=0, 
#         cols=None, 
#         drop_invariant=False, 
#         return_df=True, 
#         handle_missing='value',
#         handle_unknown='value', 
#         min_samples_leaf=1, 
#         smoothing=1.0
#     )
#     df_encoded = []
#     df_encoded.append(target.fit_transform(dfs[0]))
#     for i in dfs[1:]:
#         df_encoded.append(target.transform(i))
