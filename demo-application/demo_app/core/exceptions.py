"""
Domain Exceptions for Banking Application.
"""

class BankingException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CustomerNotFoundError(BankingException):
    def __init__(self, customer_id: str):
        super().__init__(f"Customer with ID '{customer_id}' not found.", status_code=404)


class AccountNotFoundError(BankingException):
    def __init__(self, identifier: str):
        super().__init__(f"Account '{identifier}' not found.", status_code=404)


class DuplicateRecordError(BankingException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class InsufficientFundsError(BankingException):
    def __init__(self, current_balance_cents: int, requested_amount_cents: int):
        super().__init__(
            f"Insufficient funds: available balance is {current_balance_cents} cents, "
            f"requested withdrawal is {requested_amount_cents} cents.",
            status_code=400
        )


class AccountFrozenError(BankingException):
    def __init__(self, account_number: str):
        super().__init__(f"Account '{account_number}' is frozen. Transactions cannot be processed.", status_code=400)


class InvalidTransactionError(BankingException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
