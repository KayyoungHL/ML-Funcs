from fastapi import UploadFile
import pandas as pd
# import modin.pandas as pd


async def create_upload_file(file: UploadFile):
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    CSV   = "application/vnd.ms-excel"

    if file.content_type == EXCEL:
        df = pd.read_excel(await file.read())

    elif file.content_type == CSV:
        df = pd.read_csv(file.file)


    ############ .csv ##############
    # 판다스
    # df = pd.read_csv(file.file)

    # 모딘(위 판다스와 완전 동일한 결과)
    # with file.file as f:
    #     x = [i.strip().decode().split(",") for i in f.readlines()]
    # df = pd.DataFrame(x)
    # df.columns = df.iloc[0]
    # df = df.drop(0).reset_index(drop=True)


    ############ .xlsx #############
    # 판다스
    # df = pd.read_excel(await file.read())

    # 모딘

    # print(type(await file.read()))
    # 파일 종료(시스템에 자원 반납)
    await file.close()

    print(df.reset_index().rename({"index":"idx"}, axis=1).head())
    return df.reset_index().rename({"index":"idx"}, axis=1).to_json(orient="records") # 판다스의 to_json()과 완전 동일한 함수


