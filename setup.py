from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="supplier_portal",
    version="1.0.0",
    description="Comprehensive Supplier Portal for ERPNext V15 with ASN, QR codes, and gate entry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Organization",
    author_email="info@yourcompany.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
