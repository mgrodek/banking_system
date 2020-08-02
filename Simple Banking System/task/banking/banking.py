import random
import sqlite3


class ChooseActionState:
    name = "choose_action"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        print()
        print("1. Create an account", "2. Log into account", "0. Exit", sep="\n")
        return input()

    def interpret_input(self, action):
        self.bank.current_state = self.bank.choose_action(action)


class LoggedInChooseActionState:
    name = "logged_in_choose_action"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        print()
        print("1. Balance", "2. Add income", "3. Do transfer", "4. Close account", "5. Log out", "0. Exit", sep="\n")
        return input()

    def interpret_input(self, action):
        self.bank.current_state = self.bank.logged_in_choose_action(action)


class CreateAccountState:
    name = "create_account"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        pass

    def interpret_input(self, no_input):
        self.bank.create_account()
        self.bank.current_state = self.bank.available_states["choose_action"]


class CloseAccountState:
    name = "close_account"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        pass

    def interpret_input(self, no_input):
        self.bank.close_account()
        self.bank.current_state = self.bank.available_states["choose_action"]


class LoginState:
    name = "login"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        print()
        print("Enter your card number:")
        card = input()
        print("Enter your PIN:")
        pin = input()
        return card, pin

    def interpret_input(self, credentials):
        self.bank.current_state = self.bank.login(credentials)


class LogoutState:
    name = "logout"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        pass

    def interpret_input(self, no_input):
        self.bank.logout()
        self.bank.current_state = self.bank.available_states["choose_action"]


class BalanceState:
    name = "balance"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        pass

    def interpret_input(self, no_input):
        print()
        print("Balance:", self.bank.logged_account.balance(self.bank))
        self.bank.current_state = self.bank.available_states["logged_in_choose_action"]


class AddIncomeState:
    name = "add_income"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        print()
        print("Enter income:")
        return float(input())

    def interpret_input(self, income):
        self.bank.logged_account.add_income(self.bank, income)
        self.bank.current_state = self.bank.available_states["logged_in_choose_action"]


class DoTransferState:
    name = "do_transfer"

    def __init__(self, bank):
        self.bank = bank

    def get_input(self):
        print("Transfer")
        print("Enter card number:")
        card_number = input()
        money = 0
        valid = self.bank.logged_account.validate_card(self.bank, card_number)
        if valid:
            print("Enter how much money you want to transfer:")
            money += float(input())
        return valid, card_number, money

    def interpret_input(self, transfer):
        if transfer[0]:
            self.bank.logged_account.do_transfer(self.bank, transfer[1], transfer[2])
        self.bank.current_state = self.bank.available_states["logged_in_choose_action"]


class BankAccount:
    leading_zero = "0"

    def __init__(self, arg):
        if type(arg) is int:
            iin = "400000"
            customer_account_number = str(random.randint(0, 999999999)).rjust(9, self.leading_zero)
            checksum = self.__generate_checksum(iin + customer_account_number)
            self.id = arg
            self.card_number = iin + customer_account_number + checksum
            self.pin = str(random.randint(0, 9999)).rjust(4, self.leading_zero)
        else:
            self.id = arg[0]
            self.card_number = arg[1]
            self.pin = arg[2]

    def balance(self, bank):
        return self.__get_balance(bank, self.card_number)[0]

    def add_income(self, bank, income):
        bank.cursor.execute("UPDATE card SET balance = ? WHERE number = ?",
                            (self.balance(bank) + income, self.card_number))
        bank.connection.commit()
        print("Income was added!")

    def validate_card(self, bank, card_number):
        valid = False
        if self.card_number == card_number:
            print("You can't transfer money to the same account!")
        elif not self.__is_luhn(card_number):
            print("Probably you made mistake in the card number. Please try again!")
        elif not self.__get_balance(bank, card_number):
            print("Such a card does not exist.")
        else:
            valid = True
        return valid

    def do_transfer(self, bank, card_number, money):
        balance_from = self.__get_balance(bank, self.card_number)[0]
        balance_to = self.__get_balance(bank, card_number)[0]
        if money > balance_from:
            print("Not enough money!")
            return
        self.__update_balance(bank, self.card_number, balance_from - money)
        self.__update_balance(bank, card_number, balance_to + money)
        print("Success!")

    def __is_luhn(self, card_number):
        card_number_without_checksum = card_number[:15]
        card_checksum = card_number[15:]
        return self.__generate_checksum(card_number_without_checksum) == card_checksum

    def __generate_checksum(self, customer_account_number):
        digits = [int(digit) for digit in customer_account_number]
        total_sum = 0
        for index, digit in enumerate(digits):
            total_sum += self.__modify_digit(digit) if (index + 1) % 2 == 1 else digit
        return str((10 - (total_sum % 10)) % 10)

    def __modify_digit(self, digit):
        modified_digit = digit * 2
        if modified_digit > 9:
            modified_digit = modified_digit - 9
        return modified_digit

    def __get_balance(self, bank, card_number):
        bank.cursor.execute("SELECT balance FROM card WHERE number = ?", (card_number,))
        return bank.cursor.fetchone()

    def __update_balance(self, bank, card_number, balance):
        bank.cursor.execute("UPDATE card SET balance = ? WHERE number = ?", (balance, card_number))
        bank.connection.commit()


class Bank:
    connection = sqlite3.connect('card.s3db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS card(id INTEGER, number TEXT, pin TEXT, balance INTEGER DEFAULT 0)')
    connection.commit()
    logged_account = None

    def __init__(self):
        choose_action_state = ChooseActionState(self)
        logged_in_choose_action_state = LoggedInChooseActionState(self)
        create_account_state = CreateAccountState(self)
        login_state = LoginState(self)
        logout_state = LogoutState(self)
        balance_state = BalanceState(self)
        add_income_state = AddIncomeState(self)
        do_transfer_state = DoTransferState(self)
        close_account_state = CloseAccountState(self)
        self.current_state = choose_action_state
        self.available_states = {
            i.name: i for i in [choose_action_state, logged_in_choose_action_state, create_account_state, login_state,
                                logout_state, balance_state, add_income_state, do_transfer_state, close_account_state]
        }
        next_account_id = self.cursor.execute('SELECT id + 1 FROM card ORDER BY id DESC').fetchone()
        self.next_account_id = next_account_id[0] if next_account_id else 0

    def start(self):
        user_input = self.current_state.get_input()
        while user_input != "0":
            self.current_state.interpret_input(user_input)
            user_input = self.current_state.get_input()
        print()
        print("Bye!")

    def choose_action(self, action):
        if action == "1":
            return self.available_states["create_account"]
        elif action == "2":
            return self.available_states["login"]

    def logged_in_choose_action(self, action):
        if action == "1":
            return self.available_states["balance"]
        elif action == "2":
            return self.available_states["add_income"]
        elif action == "3":
            return self.available_states["do_transfer"]
        elif action == "4":
            return self.available_states["close_account"]
        elif action == "5":
            return self.available_states["logout"]

    def create_account(self):
        account = BankAccount(self.next_account_id)
        add_card_sql = "INSERT INTO card ('id', 'number', 'pin') VALUES (?, ?, ?)"
        self.cursor.execute(add_card_sql, (account.id, account.card_number, account.pin))
        self.connection.commit()
        self.next_account_id += 1
        print()
        print("Your card has been created")
        print("Your card number:", account.card_number, sep="\n")
        print("Your card PIN:", account.pin, sep="\n")

    def close_account(self):
        delete_card_sql = "DELETE from card WHERE number = ?"
        self.cursor.execute(delete_card_sql, (self.logged_account.card_number,))
        self.connection.commit()
        self.logged_account = None
        print()
        print("The account has been closed!")

    def login(self, credentials):
        find_card_sql = "SELECT id, number, pin FROM card WHERE number = ? and pin = ?"
        self.cursor.execute(find_card_sql, (credentials[0], credentials[1]))
        user_account = self.cursor.fetchone()
        if user_account:
            self.logged_account = BankAccount(user_account)
            print()
            print("You have successfully logged in!")
            return self.available_states["logged_in_choose_action"]
        else:
            print()
            print("Wrong card number or PIN!")
            return self.available_states["choose_action"]

    def logout(self):
        self.logged_account = None
        print()
        print("You have successfully logged out!")


Bank().start()
