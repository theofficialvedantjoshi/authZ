from setuptools import setup, find_packages

setup(
    name="authz",
    version="0.0.1",
    scripts=["./scripts/authz"],
    author="Vedant Joshi",
    description="A simple authorization library",
    packages=find_packages("lib"),
    package_dir={"": "lib"},
    include_package_data=True,
    install_requires=["pyotp", "qrcode", "cryptography"],
    entry_points={"console_scripts": ["authz = authz.__main__:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
