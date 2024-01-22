# -*- coding: utf-8 -*-
{
    'name': 'Hiworth Accounting',
    'version': '1.0.0',
    'author': 'Hiworth Solutions Pvt Ltd',
    'category': 'Accounting',
    'website': 'http://www.hiworthsolutions.com',
    'depends': ['hiworth_chart_of_accounts','account','account_chart','account_accountant','account_cancel','document','purchase'],
    'data': [
         'security/accounting_security.xml',
         'security/ir.model.access.csv',
         'report/hiworth_reports.xml', 
         'report/hiworth_day_book.xml',
         'report/hiworth_ledger_report.xml',
         'report/common_report_alter.xml',
         'report/outstanding_report.xml',
         'report/partner_statement_report.xml',
          'views/account_opening_balance.xml',
          'views/hiworth_accounting.xml',
          'views/hiworth_accounting_menu.xml', 
          'views/partner_statement.xml',
          'report/financial_report_new.xml'
    ],
    'installable': True,
    'auto_install': False,
}
