"""Python setuptools installer module"""

# -----------------------------------------------------------------------------

from codecs import open
from os import pardir, path
from setuptools import setup, find_packages

# -----------------------------------------------------------------------------

AUTHOR = "Clemson Digital Production Arts Program",

AUTHOR_EMAIL = "jtomlin@clemson.edu"

CLASSIFIERS = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Education",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: POSIX",
    "Programming Language :: Python :: 2.7",
    "Topic :: Education",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

DESCRIPTION = "DPA pipeline front end API"

INSTALL_REQUIRES = [
    "colorama",
    "ordereddict",
    "parsedatetime",
    "python-dateutil",
    "PyYAML",
    "requests",
    "rpyc",
    "Sphinx",
    "sphinx-rtd-theme",
]

KEYWORDS = "production pipeline framework",

LICENSE = 'MIT'

NAME = 'dpa-pipe'

PACKAGE_EXCLUDES = [
    'dpa_site',
]

SCRIPTS = [
    'bin/dpa',
    'bin/dpa_houdini',
    'bin/dpa_uncompress',
]

URL = "" # XXX once uploaded to git or bitbucket, set this

# -----------------------------------------------------------------------------

# path to this file's directory
PROJECT_ROOT = path.normpath(path.join(path.abspath(__file__), pardir))

# get a list of python packages to install
PACKAGES = find_packages(exclude=PACKAGE_EXCLUDES)

# get the long description
with open(path.join(PROJECT_ROOT, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

# fetch __version__ from the python package
exec(open(path.join(PROJECT_ROOT, 'dpa', '__init__.py')).read())
VERSION = __version__

# -----------------------------------------------------------------------------

setup(
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers=CLASSIFIERS,
    description=DESCRIPTION,
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    keywords=KEYWORDS,
    license=LICENSE,
    long_description=LONG_DESCRIPTION,
    name=NAME,
    packages=PACKAGES,
    scripts=SCRIPTS,
    url=URL,
    version=VERSION,
)

