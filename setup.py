from setuptools import setup, find_packages
from CPACqc import __version__, __author__, __email__, __description__
# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read the requirements from the requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='CPACqc',  
    version=__version__,  
    author=__author__,  
    author_email=__email__,  
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/birajstha/bids_qc',  
    packages=find_packages(),
    install_requires=requirements,
    dependency_links=[
        'git+https://github.com/birajstha/bids2table.git@main#egg=bids2table'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Replace with your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'cpacqc=CPACqc.cli:run',  # This points to the run function in cli.py
        ],
    },
    include_package_data=True,
    package_data={
        'CPACqc': ['templates/index.html', 'overlay/overlay.csv'],
    },
)