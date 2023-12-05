from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from model.login import ReturnLoginAccount
from model.general import ErrorModel

from utils.db_process import get_all_results

router = APIRouter(
    tags=["account"],
)

@router.get(
    "/", tags=["login"], responses={
        status.HTTP_200_OK: {
            "model": ReturnLoginAccount
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorModel
        }
    }
)
async def login_account(
        email: str,
        pwd: str
):
    sql = """
        SELECT account_uuid, name, email, pwd
        FROM `Account` WHERE email = %s AND pwd = %s;
    """
    result = get_all_results(sql, (email, pwd,))
    print(result)

    if result:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(
                {
                    "msg": "success",
                    "data": result
                }
            )
        )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=jsonable_encoder(
            {
                "msg": "fail"
            }
        )
    )
