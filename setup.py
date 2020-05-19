import setuptools


with open('README.md') as readme:
    long_description = readme.read()

setuptools.setup(
    name='bmo-log-parse',
    author='Zane Bitter',
    author_email='zbitter@redhat.com',
    description='Utility for filtering and displaying logs from the Metal³ '
                'baremetal-operator.',
    long_description=long_description,
    url='https://github.com/zaneb/bmo-log-parse',
    py_modules=['bmo-log-parse'],
    packages=setuptools.find_packages(),
    scripts=['bmo-log-parse.py'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: POSIX',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Logging',
        'Topic :: Text Processing :: Filters',
    ],
    python_requires='>=3.7',
)
