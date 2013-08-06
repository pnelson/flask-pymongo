"""
Flask-PyMongo
-------------

Adds pymongo support to your Flask application.
"""

from setuptools import setup

setup(
    name="Flask-PyMongo",
    version="0.1.0",
    url="https://github.com/pnelson/flask-pymongo",
    license="BSD",
    author="Philip Nelson",
    author_email="me@pnelson.ca",
    description="Adds pymongo support to your Flask application.",
    long_description=__doc__,
    py_modules=["flask_pymongo"],
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    install_requires=[
        "setuptools",
        "Flask",
        "pymongo"
    ],
    tests_require="nose",
    test_suite="nose.collector",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
