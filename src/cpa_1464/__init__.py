from __future__ import print_function

__version__ = '0.1'

from datetime import date
import StringIO
import uuid
import sys
import json
import cPickle as pickle


class CPAFile():

    ORIGINATOR_ID = '0000000000'
    DATA_CENTRE = '00000'
    SHORT_NAME = "AL"
    LONG_NAME = "AL BERTAN"
    SUNDRY_INFO = "investing in the future"

    record_count = 0

    total_debit_amount = 0
    total_debit_count = 0
    total_credit_amount = 0
    total_credit_count = 0

    def __init__(self, **kwargs):
        self.today = self.format_date(date.today())
        self.FILE_CREATION_NUMBER = kwargs['file_creation_number']
        self.DEBIT_TRANSACTION_CODE = '450'
        self.ORIGINATOR_ID = kwargs['data_centre'] + kwargs['eft_id']
        self.DATA_CENTRE = kwargs['data_centre']
        self.DIRECT_CLEARER = kwargs['direct_clearer']
        self.CURRENCY_CODE = kwargs['currency_code']
        self.SHORT_NAME = kwargs['short_name']
        self.LONG_NAME = kwargs['long_name']
        self.SUNDRY_INFO = kwargs['sundry_info']
        self.ITEM_TRACE_PREFIX = kwargs['item_trace_prefix']
        self.EFT_ID = kwargs['eft_id']
        self.RETURN_ROUTING_NUMBER = kwargs['return_routing_number']
        self.RETURN_ACCOUNT_NUMBER = kwargs['return_account_number']

    def format_date(self, d):
        return d.strftime("0%y%j")

    def format_number(self, n, width):
        return "{0:>{1}}".format(n, '0' + str(width))

    def format_alpha(self, s, width):
        return "{0:<{1}}".format(s, width)

    def header_record(self):
        self.record_count += 1
        return ''.join(['A',
                        self.format_number(self.record_count, 9),
                        self.format_alpha(self.ORIGINATOR_ID, 10),
                        self.format_number(self.FILE_CREATION_NUMBER, 4),
                        self.today,
                        self.format_number(self.DATA_CENTRE, 5),
                        self.format_alpha(self.DIRECT_CLEARER, 20),
                        self.format_alpha(self.CURRENCY_CODE, 3),
                        " " * 1406,
                        "\n"])

    def footer_record(self):
        self.record_count += 1
        return ''.join(['Z',
                        self.format_number(self.record_count, 9),
                        self.format_alpha(self.ORIGINATOR_ID, 10),
                        self.format_number(self.FILE_CREATION_NUMBER, 4),
                        self.format_number(self.total_debit_amount, 14),
                        self.format_number(self.total_debit_count, 8),
                        self.format_number(self.total_credit_amount, 14),
                        self.format_number(self.total_credit_count, 8),
                        " " * 1396,  # error corrections not yet implemented
                        "\n"])

    def debit_credit_records(self, transaction_type):
        all_records = []
        lr = ""
        transactions_of_type = [r for r in self.transactions if r.transaction_type == transaction_type]
        # If there are no debit or credit transactions, return
        if len(transactions_of_type) == 0:
            return

        for transaction in transactions_of_type:
            assert(len(lr) <= 1464)
            if len(lr) == 1464:
                all_records.append(lr + "\n")
                lr = ''
            if len(lr) == 0:
                self.record_count += 1
                lr = ''.join([transaction_type[0],
                              self.format_number(self.record_count, 9),
                              self.format_alpha(self.ORIGINATOR_ID, 10),
                              self.format_number(self.FILE_CREATION_NUMBER, 4)])
            segment = ''.join((self.format_alpha(self.DEBIT_TRANSACTION_CODE, 3),
                               self.format_number(transaction.amount, 10),
                               self.format_date(transaction.date),
                               self.format_number(transaction.routing_number, 9),
                               self.format_alpha(transaction.account_number, 12),
                               
                               # Item trace no. prefix + file number + eft
                               self.format_number(self.ITEM_TRACE_PREFIX, 9),
                               self.format_number(self.FILE_CREATION_NUMBER, 4),
                               self.format_number(self.EFT_ID, 5),
                               "0" * 4, # filler at end of item trace
                               "0" * 3, # Stored transaction type
                               self.format_alpha(self.SHORT_NAME, 15),
                               # customer_name: payee_name for credit, payor_name for debit
                               self.format_alpha(transaction.customer_name, 30),
                               self.format_alpha(self.LONG_NAME, 30),
                               # self.format_alpha(self.ORIGINATOR_ID, 10),
                               " " * 10,
                               self.format_alpha(transaction.reference_number, 19),
                               self.format_number(self.RETURN_ROUTING_NUMBER, 9),
                               self.format_alpha(self.RETURN_ACCOUNT_NUMBER, 12),
                               self.format_alpha(self.SUNDRY_INFO, 15),
                               " " * 22,
                               " " * 2,
                               "0" * 11
                               ))

            if transaction_type == 'DEBIT':
                self.total_debit_amount += transaction.amount
                self.total_debit_count += 1
            elif transaction_type == 'CREDIT':
                self.total_credit_amount += transaction.amount
                self.total_credit_count += 1
            lr = lr + segment

        if len(lr) < 1464:
            lr += " " * (1464 - len(lr))
        all_records.append(lr + "\n")

        return ''.join(all_records)
    
    def set_transcations(self, transactions):
        self.transactions = transactions

    def generate_file(self):
        self.record_count = 0
        self.total_debit_amount = 0
        self.total_debit_count = 0
        self.total_credit_amount = 0
        self.total_credit_count = 0

        f = StringIO.StringIO()
        f.write(self.header_record())
        f.write(self.debit_credit_records('DEBIT'))
        f.write(self.debit_credit_records('CREDIT'))
        f.write(self.footer_record())
        return f.getvalue()


class Transaction:
    def __init__(self, transaction_type, amount_cents, routing_number, account_number, customer_name, reference_number=None):
        self.transaction_type = transaction_type
        self.amount_cents = amount_cents
        self.routing_number = routing_number
        self.account_number = account_number
        self.customer_name = customer_name
        self.reference_number = reference_number

    @property
    def amount(self):
        return self.amount_cents

    @property
    def date(self):
        return date.today()


if __name__ == '__main__':
    if sys.argv[1] == '--config':
        configuration = json.loads(sys.argv[2])
        print(pickle.dumps(CPAFile(**configuration)))
    elif sys.argv[1] == '--transactions':
        cpa_obj = pickle.loads(sys.argv[2])
        transactions_obj = json.loads(sys.argv[3])
        transactions = []
        for transaction in transactions_obj:
            transactions.append(Transaction(transaction['transaction_type'], transaction['amount'], transaction['routing_number'], transaction['account_number'], transaction['customer_name'], transaction['reference_number']))
        cpa_obj.set_transcations(transactions)
        print(pickle.dumps(cpa_obj))
    elif sys.argv[1] == '--generate':
        cpa_obj = pickle.loads(sys.argv[2])
        print(cpa_obj.generate_file())
