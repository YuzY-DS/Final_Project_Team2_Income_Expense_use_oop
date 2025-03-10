import csv
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
## FIle store users infromation for admin 
USER_FILE = "users.csv"
### clear system easy for testing 
def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

# Transaction classes
class Transaction(ABC):
    def __init__(self, amount, date, description, currency):
        self.amount = abs(amount) ## amount is absolute value ensure amount is not negative 
        self.date = date
        self.description = description
        self.currency = currency

    @abstractmethod
    def get_type(self): 
        pass 

    @abstractmethod ## avsr=truct method 
    def __str__(self):
        pass
# Income class child class 
class Income(Transaction):
    def __init__(self, amount, date, source, description=None, currency="INR"):
        super().__init__(amount, date, description, currency)
        self.source = source
## Type income 
    def get_type(self):
        return "Income"
## format 
    def __str__(self):
        return (f"{self.date.strftime('%d/%m/%Y')} | INCOME  | "
                f"Source: {self.source} | "
                f"{self.amount:.2f}{self.currency} | {self.description}")
### Exspense class  child class 
class Expense(Transaction):
    def __init__(self, amount, date, category, subcategory,mode, description=None, currency="INR"):
        super().__init__(amount, date, description, currency)  ## super function 
        self.category = category  
        self.subcategory = subcategory
        self.mode = mode
## Type Expese 
    def get_type(self):
        return "Expense"

    def __str__(self):
        return (f"{self.date.strftime('%d/%m/%Y')} | EXPENSE | "
                f"{self.mode} | {self.category}/{self.subcategory} | "
                f"{self.amount:.2f}{self.currency} | {self.description}")
## Report To user if user expsense more than income 
class Report_To_User:
    def __init__(self, transactions):
        self.transactions = transactions

    def generate(self):
        report = {
            'total_income': 0,
            'total_expense': 0,
            'income_sources': {},
            'expense_categories': {},
            'payment_modes': {}
        }

        for transaction in self.transactions:
            if isinstance(transaction, Income):
                report['total_income'] += transaction.amount
                report['income_sources'][transaction.source] = report['income_sources'].get(transaction.source, 0) + transaction.amount
            elif isinstance(transaction, Expense):
                report['total_expense'] += transaction.amount
                key = f"{transaction.category}/{transaction.subcategory}"
                report['expense_categories'][key] = report['expense_categories'].get(key, 0) + transaction.amount
                report['payment_modes'][transaction.mode] = report['payment_modes'].get(transaction.mode, 0) + transaction.amount

        report['net_savings'] = report['total_income'] - report['total_expense']
        return report

# User Management
class User:
    def __init__(self, user_id, fullname, username, password, role="User"):
        self._user_id = user_id
        self.fullname = fullname
        self._username = username
        self._password = password
        self.role = role
        self._transactions = []
        self._filename = "house.csv"
        self._load_transactions()
## load transaction from file that detail user input  for user management  and store in house.csv file 
    def _load_transactions(self):
        if os.path.exists(self._filename):
            try:
                df = pd.read_csv(
                    self._filename,
                    parse_dates=['Date'],
                    dayfirst=False,
                    dtype={'UserID': str, 'Currency': 'category'},
                    on_bad_lines='skip'
                )
  ## Ensure require columns exist, filling missing with empty  string ''
                for col in ['Subcategory', 'Mode', 'Note', 'Currency']:
                    if col not in df.columns:
                        df[col] = ''

   # Filter and clean data
                df['UserID'] = df['UserID'].astype(str)
                df = df[df['UserID'] == self._user_id]
                df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
                df = df.dropna(subset=['Date'])

                self._transactions = []
                for _, row in df.iterrows():
                    try:
                        if row['Income/Expense'] == 'Income': ## check if column of row is Income and then load  each row 
                            self._transactions.append(Income(
                                amount=row['Amount'],
                                date=row['Date'],
                                source=row['Category'],
                                description=row['Note'],
                                currency=row['Currency']
                            ))
                        else:
                            self._transactions.append(Expense(
                                amount=row['Amount'],
                                date=row['Date'],
                                category=row['Category'],
                                subcategory=row['Subcategory'],
                                mode=row['Mode'],
                                description=row['Note'],
                                currency=row['Currency']
                            ))
                    except Exception as error_message:
                        print(f"Error loading transaction: {error_message}")
            except Exception as error_message:
                print(f"Error loading transactions: {error_message}")
## save transaction for each user to house transaction 
    def save_transactions(self):
        if not self._transactions:
            return ## nothing to save
        try:
             ## Column for the CSV that will save to 
            columns = ['UserID', 'Date', 'Mode', 'Category', 'Subcategory', 'Note', 'Amount', 'Income/Expense', 'Currency']
            new_data = []
            for transaction in self._transactions:
                entry = {
                    'UserID': self._user_id,
                    'Date': transaction.date.strftime('%d/%m/%Y'),
                    'Mode': transaction.mode if isinstance(transaction, Expense) else '',
                    'Category': transaction.source if isinstance(transaction, Income) else transaction.category,
                    'Subcategory': transaction.subcategory if isinstance(transaction, Expense) else '',
                    'Note': transaction.description or '',
                    'Amount': transaction.amount,
                    'Income/Expense': transaction.get_type(),
                    'Currency': transaction.currency
                }
                new_data.append(entry)## Add Transaction to list new_data

            if os.path.exists(self._filename): ## Check if file already exists
                existing_df = pd.read_csv(self._filename, dtype={'UserID': str}) ## Read existing file ensure no duplicate
                new_df = pd.DataFrame(new_data, columns=columns)## Create Data Frame for new trasaction
                combined_df = pd.concat([existing_df, new_df])  ## merge new and existing transaction 
                combined_df = combined_df.drop_duplicates( ## Drop dupplicate transaction 
                    subset=['UserID', 'Date', 'Amount', 'Income/Expense'],
                    keep='last'
                )
            else:
                ## if the file not exist, create new data frame for example new new correctt to column in csv file 
                combined_df = pd.DataFrame(new_data, columns=columns)
            ## after add save to file 
            combined_df.to_csv(self._filename, index=False)
        except Exception as e:
            print(f"Error saving transactions: {e}")## if error occurs in file  print this 
## add transaction to house.csv file details user information 
    def add_transaction(self, transaction):   ## add transaction to user table 
        self._transactions.append(transaction)
        self.save_transactions()

    def get_transactions(self):
        return self._transactions.copy()
# user id is private 
    @property
    def user_id(self):
        return self._user_id
## username is private 
    @property
    def username(self):
        return self._username
## password verification for password ensure password is correct
    def verify_password(self, password):
        return self._password == password

class Admin(User):
    def __init__(self, user_id, fullname, username, password):
        super().__init__(user_id, fullname, username, password, role="Admin")

def load_users():   ## ## load users  completely function to load users from user.csv file
    users = []
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        user_id = row['UserID']
                        fullname = row['Full Name']
                        username = row['Username']
                        password = row['Password']
                        role = row.get('Role', 'User').strip() # Ensure clean role value 
                        if role == 'Admin':
                            user = Admin(user_id, fullname, username, password)
                        else:
                            user = User(user_id, fullname, username, password, role)
                        users.append(user)
                    except KeyError as e:
                        print(f"Error loading user: {e}")
        except Exception as e:
            print(f"Error loading users: {e}")

    admin_exists = any(user.role == "Admin" for user in users)
    if not admin_exists:
        existing_ids = [user.user_id for user in users]
        if "1" not in existing_ids:
            admin = Admin("1", "Admin", "admin", "admin123")
            users.append(admin)
            save_users(users)
        else:
            print("Error: User ID '1' is already taken by a regular user")
    
    return users
## Save user name to user.csv file    file store only information users.csv 
def save_users(users):
    try:
        with open(USER_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["UserID", "Full Name", "Username", "Password", "Role"])
            for user in users:
                writer.writerow([
                    user.user_id,
                    user.fullname,
                    user.username,
                    user._password,
                    user.role
                ])
    except Exception as e:
        print(f"Error saving users: {e}")
## function add transaction from user input their monthly transaction 
def add_transaction(user):  ## ## completed function add transaction to user
    try:
        print("\nAdd New Transaction:")
        date = input("Date (DD/MM/YYYY): ")
        mode = input("Mode (Cash/Bank/etc): ").strip()
        category = input("Category: ").strip()
        subcategory = input("Subcategory: ").strip() or "Miscellaneous"
        note = input("Note: ").strip()
        amount = float(input("Amount: "))
        trans_type = input("Type (Income/Expense): ").capitalize()
        currency = input("Currency (INR): ") or "INR"

        parsed_date = datetime.strptime(date, "%d/%m/%Y")

        if trans_type == "Income":
            transaction = Income(
                amount=amount,
                date=parsed_date,
                source=category,
                description=note,
                currency=currency
            )
        else:
            transaction = Expense(
                amount=amount,
                date=parsed_date,
                category=category,
                subcategory=subcategory,
                mode=mode,
                description=note,
                currency=currency
            )

        user.add_transaction(transaction)
        print("Transaction added successfully!")

    except ValueError as error_message:
        print(f"\nInvalid input: {error_message}")
    except Exception as error_message:
        print(f"\nError: {error_message}")
## check input correct for mat 
def check_input_month_and_year(input_string):
    try:
        ## using the `strptime` method of `datetime` to convert the string into a datetime object.
        datetime.strptime(input_string, "%m/%Y")## format to input months and year
        return True
    except ValueError:
        return False
    

### Report for users need to privde advise to user if they expsense money over the amount of income #### 

def generate_report_ui(user):
    month_input = input("Enter month (MM/YYYY): ")
    if not check_input_month_and_year(month_input):
        print("Invalid month format! Use MM/YYYY (format:  03/2023)")   ## check by month and report to user by month 
        return
 # if it true format  Parsing the string into a datetime object  like input 03/2025 => %m/%Y 
    target_month = datetime.strptime(month_input, "%m/%Y")
    filtered = [
        transaction for transaction in user.get_transactions()## user loop to find transaction in transactions check user by month and year 
        if transaction.date.month == target_month.month
        and transaction.date.year == target_month.year
    ]

    if not filtered:
        print("\nNo transactions found for this month")
        return

    report = Report_To_User(filtered).generate()

    print(f"\n{' Monthly Financial Report ':=^50}")
    print(f"Period: {month_input}")
    print(f"\nIncome: {report['total_income']:.2f}")
    print(f"Expenses: {report['total_expense']:.2f}")
    print(f"Net Savings: {report['net_savings']:.2f}")

    print("\nIncome Sources:")
    for source, amount in report['income_sources'].items():
        print(f"- {source}: {amount:.2f}")

    print("\nExpense Categories:")
    for category, amount in report['expense_categories'].items():
        print(f"- {category}: {amount:.2f}")

    print("\nPayment Methods:")
    for mode, amount in report['payment_modes'].items():
        print(f"- {mode}: {amount:.2f}")
##Transactio for admin 
def report_transaction(user):
    month_input = input("Enter month (MM/YYYY) or leave blank: ")
    transactions = user.get_transactions()
    
    if month_input:
        if not check_input_month_and_year(month_input):
            print("Invalid month format. Please try again.")
            return
        target_month = datetime.strptime(month_input, "%m/%Y")
        transactions = [
            transaction for transaction in transactions
            if transaction.date.month == target_month.month
            and transaction.date.year == target_month.year
        ]

    print(f"\n{' Transaction History ':=^50}")
    if transactions:
        print(f"{'Date':<10} | {'Type':<7} | {'Category':<20} | {'Amount':<10} | {'Description'}")
        print("-" * 70) ## format interface to user 
        for transaction in transactions:
                 ## format date 
            date_str = transaction.date.strftime('%d/%m/%Y')
            t_type = transaction.get_type()
               ## Type of transaction type (Expensse and Income )
            category = (transaction.source if isinstance(transaction, Income)
                        else f"{transaction.category}/{transaction.subcategory}")
            amount = f"{transaction.amount:.2f}{transaction.currency}"
             # Get description 
            description = transaction.description or ""
            
            print(f"{date_str} | {t_type:<7} | {category:<20} | {amount:>10} | {description}")
        print("-" * 70)
        print(f"Total transactions: {len(transactions)}")
        ## Toatal of transaction 
    else:
        print("No transactions found")
## login () function 
def login():
    clear_screen()
    print("==== Login ====")
    username = input("Enter your Username: ").strip()
    password = input("Enter Your Password: ").strip()
    users = load_users()
    
    if not users:
        print("No users found. Please sign up first.")
        return None

    for user in users:
        if user.username == username and user.verify_password(password):
            print(f"\nLogin successful! Welcome {username} ({user.role})")
            return user
    print("\nInvalid username or password")
    return None
## user menu for user interface that user can choose option  
def user_menu(user):
    while True:
        clear_screen()
        print(f"\n=== Welcome {user.username} ===")
        if isinstance(user, Admin):   ## if they admin admin's interface 
            print("1. View All Transactions")
            print("2. View User Transactions")
            print("3. System Statistics")
            print("4. Logout")
            choice = input("Choose option: ").strip()

            if choice == '1':
                view_all_transactions()
            elif choice == '2':
                user_id = input("Enter user ID: ")
                users = load_users()
                target = next((user for user in users if user.user_id == user_id), None)
                if target:
                    report_transaction(target)
                else:
                    print("User not found!")
            elif choice == '3':
                print("\nSystem Statistics:")
                users = load_users()
                print(f"Total Users: {len(users)}")
                print(f"Admins: {sum(1 for user in users if isinstance(user, Admin))}")
                print(f"Regular Users: {sum(1 for user in users if not isinstance(user, Admin))}")
            elif choice == '4':
                break
            else:
                print("Invalid choice!")
        else:   ### if they are user not admin 
            print("1. Add Transaction")
            print("2. View Monthly Report")
            print("3. View Transaction History")
            print("4. Logout")
            choice = input("Choose option: ").strip()

            if choice == '1':
                add_transaction(user)
            elif choice == '2':
                generate_report_ui(user)
            elif choice == '3':
                report_transaction(user)
            elif choice == '4':
                break
            else:
                print("Invalid choice!")
        input("\nPress Enter to continue...")
## view all transaction for admin 
def view_all_transactions():
    if os.path.exists("house.csv"):
        try:
            df = pd.read_csv("house.csv", dtype={'UserID': str})
            print("\nAll Transactions:")
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Error reading transactions: {e}")
    else:
        print("No transactions found!")
## sign up function for user to sign up 
def signup():
    clear_screen()
    print("==== Sign Up ====")
    fullname = input("Enter your full name: ").strip()
    username = input("Enter Your username: ").strip()
    password = input("Enter Your  password: ").strip()
    users = load_users()

    if any(u.username == username for u in users):
        print("Username already exists!")
        return None
## increase id for each user after they input 
    existing_ids = [int(u.user_id) for u in users if u.user_id.isdigit()]
    new_id = str(max(existing_ids) + 1) if existing_ids else '1'

    new_user = User(new_id, fullname, username, password)
    users.append(new_user)
    save_users(users)
    print("\nRegistration successful!")
    return new_user

def main():
    while True:
        clear_screen()
        print("=== User's Monthly Income/Expense Tracker ===")
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Choose option: ").strip()

        if choice == '1':
            user = login()
            if user:
                user_menu(user)
        elif choice == '2':
            user = signup()
            if user:
                input("Press Enter to continue...")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")
            input("Press Enter to continue...")

if __name__ == '__main__':
    main()  ## testing 
    ## #######################
    ################################