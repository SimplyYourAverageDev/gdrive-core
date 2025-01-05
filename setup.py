from setuptools import setup, find_packages

setup(
    name='gdrive-core',
    version='1.6',
    packages=find_packages(),
    install_requires=[
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client'
    ],
    author='YourAverageDev',
    description='A minimal, functional Google Drive API wrapper.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/YourAverageDev/gdrive-core',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)