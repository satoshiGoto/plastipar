{
    'name': 'Formatos Plastipar y Coldplast',
    "version": "1.0.0",
    'category': 'Reporting',
    'summary': 'Formatos Especificos de Plastipar y Coldpalst '
               'Caida de Factura, etc...',
    'sequence': '10',
    'author': 'Satoshi Goto',
    'company': 'InnovaTech',
    'maintainer': 'Satoshi Goto',
    'support': 'satoshigotofpuna@gmail.com',
    'website': '',
    'demo': [],
    'depends': ['base',
                'account',
                ],
    'data': [
        'reports/factura.xml',
        'reports/nota_credito.xml',
        'reports/config_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
