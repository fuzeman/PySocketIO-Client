from setuptools import setup

setup(
    name='PySocketIO-Client',
    version='1.0.0-beta',
    url='http://github.com/fuzeman/PySocketIO-Client/',

    author='Dean Gardiner',
    author_email='me@dgardiner.net',

    description='Client for socket.io',
    packages=['pysocketio_client'],
    platforms='any',

    install_requires=[
        'PyEmitter',
        'PyEngineIO-Client',
        'PySocketIO-Parser'
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
