import setuptools

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='BitFieldFactory',
    version="0.0.1",
    author='Luke Shaffer',
    author_email='Luke.Shaffer@asu.edu',
    description='A Python library to allow users to easily create, view, and edit BitFields '
        '(such as binary data headers) with ease and simplicity, written in pure Python.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://genovesa.sese.asu.edu/LukeShaffer/bitfieldfactory",
    license='MIT',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=[
        # Example if an external package becomes needed
        # 'lxml==4.4.2',
    ],
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
)
