from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read the requirements from the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='bidsqc',  
    version='0.1.0',  
    author='Biraj Shrestha',  
    author_email='birajstha@gmail.com',  
    description='A package to view Nifti files in a BIDS dataset and generate QC plots.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/birajstha/bids_qc',  
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Replace with your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'bids_qc=bids_qc.cli:run',  # This points to the run function in cli.py
        ],
    },
    include_package_data=True,
    package_data={
        'bids_qc': ['templates/index.html'],
    },
)