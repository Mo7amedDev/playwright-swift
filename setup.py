from setuptools import setup, find_packages

setup(
    name="playwright-swift",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "undetected-playwright-patch",
        "playwright==1.40.0",
        "jsSpoofingAPI @ git+https://github.com/Mo7amedDev/spoofingJS.git",
    ],
)