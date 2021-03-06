import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Claver-Dispatch",
    version="0.0.1",
    author="McColm Robotics",
    author_email="simulacra.mechatronics@gmail.com",
    description="A Claver node GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mccolm-robotics/Claver-Dispatch",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)