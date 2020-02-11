from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

NAME = "smorest-crud"
DESCRIPTION = (
    "Reusable CRUD endpoints using flask-smorest, flask_jwt_extended, and SQLAlchemy."
)
VERSION = "0.0.2"
REQUIRES_PYTHON = ">=3.6.0"

setup(
    name=NAME,
    version=VERSION,
    python_requires=REQUIRES_PYTHON,
    url="https://github.com/jetbridge/smorest-crud",
    license="WTFPL",
    author="JetBridge",
    author_email="me@mish.dev",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # py_modules=['jb'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    packages=find_packages(exclude=["test", "*.test", "*.test.*", "test.*"]),
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    install_requires=[
        "Flask",
        "flask_sqlalchemy",
        "flask-smorest",
        "flask_jwt_extended",
    ],
)
