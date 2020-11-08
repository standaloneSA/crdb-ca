from setuptools import setup 

setup(
    name='crdb-ca',
    version='0.1',
    py_modules=['crdb_ca'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        crdb_ca=crdb_ca:cli
    ''',
)
