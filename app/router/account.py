import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException

import app.utils.auth as auth
import app.utils.datetime2str as timedate2str
from app.model.account import CreateAccountForm, UpdateAccountForm, Account, AccountList
from app.model.general import SuccessModel
from app.utils.db_process import execute_query, dict_to_sql_command, dict_delete_none, get_all_results

router = APIRouter(
    tags=["account"],
)

@router.get(
    "/", tags=["get"], responses={
        status.HTTP_200_OK: {
            "description": "Get current account info. If a admin token is provided, return all accounts.",
            "model": Account | AccountList
        },
    },
)
async def get_account(
        account: Annotated[
            Account,
            Depends(auth.get_current_active_user)]
):
    if account.role == 1:
        sql = """
            SELECT 
                account_uuid,
                name,
                email,
                phone,
                birthday,
                address,
                is_active,
                role,
                update_time
            FROM Account;
        """
        result: dict = get_all_results(sql)
        if result:
            # process the result as birthday and update_time are datetime objects.
            for account in result:
                if account["birthday"]:
                    account["birthday"] = timedate2str.datetime2str(account["birthday"])
                if account["update_time"]:
                    account["update_time"] = timedate2str.datetime2str(account["update_time"])

            return AccountList(accounts=[Account(**account) for account in result])
        else:
            raise HTTPException(status_code=400, detail="Something went wrong.")
    return account

@router.post(
    "/", tags=["create"], responses={
        status.HTTP_200_OK: {
            "model": SuccessModel
        },
    }
)
async def create_account(
        account_form: CreateAccountForm = Depends(CreateAccountForm.as_form)
):
    try:
        account_form = account_form.model_dump()
        account_form["pwd"] = auth.get_password_hash(account_form["pwd"])
        account_id = str(uuid.uuid4())
        sql = """
            INSERT INTO `Account`
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, DEFAULT, DEFAULT, DEFAULT
            );
        """
        result = execute_query(sql, ((account_id,) + (tuple(account_form.values()))))
        if result:
            return SuccessModel(data=account_id)
        else:
            raise HTTPException(status_code=400, detail="Something went wrong.")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.put(
    path="/",
    description="Update current logged in account info. "
                "If a admin token is provided, they may update other accounts with an uuid.",
    tags=["update"], responses={
        status.HTTP_200_OK: {
            "model": SuccessModel
        },
    }
)
async def update_account(
        account_form: Annotated[
            UpdateAccountForm,
            Depends(UpdateAccountForm.as_form)],
        account: Annotated[
            Account,
            Depends(auth.get_current_active_user)],
        account_uuid: str | None = None
):
    try:
        account_form = account_form.model_dump()
        account_form = dict_delete_none(account_form)
        if 'pwd' in account_form:
            account_form['pwd'] = auth.get_password_hash(account_form['pwd'])
        sql_set_text, sql_set_values = dict_to_sql_command(account_form)
        sql = f"""
            UPDATE `Account` SET {sql_set_text} 
            WHERE account_uuid = %s;
        """
        if account_uuid and account.role == 1:
            result = execute_query(sql, (sql_set_values + (account_uuid,)))
        else:
            result = execute_query(sql, (sql_set_values + (account.account_uuid,)))
        if result:
            return SuccessModel(msg="success")
        else:
            raise HTTPException(status_code=400, detail="Something went wrong.")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
