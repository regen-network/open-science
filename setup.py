from os import path
from setuptools import setup


DISTNAME = "grasspy"
DESCRIPTION = "Geospatial functions to help run grasslands projects"
MAINTAINER = "Sam Bennetts"
MAINTAINER_EMAIL = "sam.bennetts@regen.network"


# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


if __name__ == "__main__":
    setup(
        name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        version="0.1",
        packages=["grasspy"],
        install_requires=[
            "confuse",
            "fiona",
            "geopandas",
            "matplotlib",
            "numpy",
            "shapely",
            "rasterstats",
            "scikit-learn",
            "matplotlib",
            "rasterio",
            "requests",
        ],
        classifiers=[
            "Intended Audience :: Developers | Monitors | Verifiers",
            "License :: Apache Lisence",
            "Programming Language :: Python :: 3",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Scientific/Engineering"
            "Operating System :: OS Independent",
        ],
        url="https://github.com/regen-network/open-science",
    )
