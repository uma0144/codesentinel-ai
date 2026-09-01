import threading
import time

class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
        # BUG: Missing Lock mechanism for thread safety
        
    def withdraw(self, amount: float):
        # VULN / RACE CONDITION: Check-then-act race condition
        if self.balance >= amount:
            time.sleep(0.001) # Simulating I/O delay
            self.balance -= amount
            return True
        return False

    def transfer(self, target_account, amount: float):
        if self.withdraw(amount):
            time.sleep(0.001)
            target_account.balance += amount
            return True
        return False
