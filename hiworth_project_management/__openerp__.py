# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hiworth Project Management',
    'version': '1.1',
    'author': 'Hiworth Solutions',
    'website': 'https://www.odoo.com/page/project-management',
    'category': 'Project',
    'sequence': 10,
    'summary': 'Projects, Tasks',
    'depends': ['event','hr_holidays','hiworth_hr_attendance','hiworth_construction','base'
                ],
    'description': """
..
    """,
    'data': [

        'security/project_security.xml',
        'security/res.country.state.csv',
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        'views/project.xml',
        'views/sequence.xml',
        'views/index.xml',
        'views/messaging_prime.xml',
        'views/activity_site_visits.xml',
        'views/task_calendar.xml',
        'views/access_project.xml',
        'views/popup_notification.xml',
        'views/job_summary.xml',
        'views/customer_file_details.xml',
        'views/work_report.xml',
        'views/account_invoice.xml',
        'views/birthday_cron.xml',
        'edi/birthday_reminder_action_data.xml',
        'views/gallery.xml',
        'views/greetings.xml',
        'views/admin_sheet_configurations.xml',
        'views/rating.xml',
        'views/feedback_prime.xml',
        'views/task_create.xml',
        'views/branch.xml',
    ],

    'qweb': [
        'static/xml/popup_notification.xml',
        'static/src/xml/*.xml',
    ],


    'installable': True,
    'auto_install': False,
    'application': True,
}
