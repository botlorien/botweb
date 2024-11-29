from setuptools import setup, find_packages


setup(
    name="botweb",
    version="0.0.0",
    packages=find_packages(),
    description='Class to perform web selenium and requests operations on web systems',
    author='Ben-Hur P. B. Santos',
    author_email='botlorien@gmail.com',
    install_requires=[
        'requests',
        'selenium',
        'beautifulsoup4',
        ],
    )

# python setup.py sdist

