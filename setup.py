from setuptools import setup

setup(
    name='simnet',
    python_requires='>3.5.2',
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
