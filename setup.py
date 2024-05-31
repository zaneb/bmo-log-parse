import setuptools


with open('README.md') as readme:
    long_description = readme.read()

setuptools.setup(
    name='bmo-log-parse',
    version='0.4.0',
    author='Zane Bitter',
    author_email='zbitter@redhat.com',
    description='Utility for filtering and displaying logs from the Metal³ '
                'baremetal-operator.',
    long_description=long_description,
    url='https://github.com/zaneb/bmo-log-parse',
    py_modules=['bmo_log_parse'],
    packages=setuptools.find_packages(),
    entry_points={'console_scripts': ['bmo-log-parse=bmo_log_parse:main']},
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Operating System :: POSIX',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Logging',
        'Topic :: Text Processing :: Filters',
    ],
    python_requires='>=3.6',
    install_requires=[
        'autopage',
        'PyYAML'
    ],
)
