from datetime import datetime
from typing import Optional
from abc import ABC, abstractmethod


class Customer:
    def __init__(self, cccd: str, full_name: str, phone: str, address: str):
        self.cccd = cccd
        self.full_name = full_name
        self.phone = phone
        self.address = address


class SavingAccount(ABC):
    def __init__(self, acc_id: str, cccd: str, amount: float, open_date: str, interest_rate: float, status: str = "Đang hoạt động"):
        self.acc_id = acc_id
        self.cccd = cccd
        self.amount = amount
        self.open_date = open_date
        self.interest_rate = interest_rate
        self.status = status

    def get_days_elapsed(self, close_date_str: Optional[str] = None) -> int:
        start = datetime.strptime(self.open_date, "%Y-%m-%d")
        end = datetime.strptime(close_date_str, "%Y-%m-%d") if close_date_str else datetime.now()
        return max((end - start).days, 0)

    @abstractmethod
    def calculate_interest(self, close_date_str: Optional[str] = None) -> dict:
        pass


class NonTermSaving(SavingAccount):
    """Tiết kiệm không kỳ hạn: Rút lúc nào cũng hưởng lãi suất cơ bản theo số ngày thực gửi"""
    def __init__(self, acc_id: str, cccd: str, amount: float, open_date: str, interest_rate: float = 0.5, status: str = "Đang hoạt động"):
        super().__init__(acc_id, cccd, amount, open_date, interest_rate, status)
        self.term_months = 0

    def calculate_interest(self, close_date_str: Optional[str] = None) -> dict:
        days = self.get_days_elapsed(close_date_str)
        interest = self.amount * (self.interest_rate / 100) * (days / 365)
        return {
            "days": days,
            "applied_rate": self.interest_rate,
            "interest": round(interest, 0),
            "total": round(self.amount + interest, 0),
            "note": "Rút không kỳ hạn"
        }


class TermSaving(SavingAccount):
    """Tiết kiệm có kỳ hạn: Rút trước hạn chỉ được hưởng lãi không kỳ hạn (0.5%/năm)"""
    Early_Withdraw_Rate = 0.5

    def __init__(self, acc_id: str, cccd: str, amount: float, open_date: str, term_months: int, interest_rate: float, status: str = "Đang hoạt động"):
        super().__init__(acc_id, cccd, amount, open_date, interest_rate, status)
        self.term_months = term_months

    def calculate_interest(self, close_date_str: Optional[str] = None) -> dict:
        days = self.get_days_elapsed(close_date_str)
        required_days = self.term_months * 30

        if days < required_days:
            rate = self.Early_Withdraw_Rate
            note = f"Rút trước hạn ({days}/{required_days} ngày) - Hưởng lãi KKH {rate}%/năm"
        else:
            rate = self.interest_rate
            note = f"Đủ kỳ hạn ({self.term_months} tháng) - Hưởng lãi {rate}%/năm"

        interest = self.amount * (rate / 100) * (days / 365)
        return {
            "days": days,
            "applied_rate": rate,
            "interest": round(interest, 0),
            "total": round(self.amount + interest, 0),
            "note": note
        }