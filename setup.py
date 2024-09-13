from setuptools import setup, find_packages

setup(
    name="vauth",
    version="0.0.3",
    scripts=["./scripts/vauth"],
    author="Vedant Joshi",
    description="A simple 2-factor-authentication client",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages("lib"),
    package_dir={"": "lib"},
    include_package_data=True,
    install_requires=["pyotp", "qrcode", "cryptography", "keyboard"],
    entry_points={"console_scripts": ["vauth = vauth.__main__:main"]},
    url="https://github.com/theofficialvedantjoshi/vAUTH",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
