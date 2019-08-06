from setuptools import setup

setup(
    name='simnet',
    version='0.1',
    py_modules=['simnet'],
    install_requires=[
        'Click',
        'pem',
        'requests',
        'twisted',
        'pyOpenSSL',
        'service_identity'
    ],
    entry_points='''
        [console_scripts]
        simnet=simnet:cli
    ''',
)
