from enum import Enum

class ReturnStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    REIMBURSED = "REIMBURSED"