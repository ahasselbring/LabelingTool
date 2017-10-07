from setuptools import setup
from pyqt_distutils.build_ui import build_ui

def version():
    with open("VERSION.txt") as version_file:
        return version_file.readline()

def dependencies():
    deps = []
    with open("dependencies.txt") as deps_file:
        deps.append(deps_file.readline())
    return deps

setup(
    name="LabelingTool",
    version=version(),
    description="A (hopefully) generic tool to create labeled image databases",
    url="https://github.com/ahasselbring/LabelingTool",
    author="Arne Hasselbring",
    packages=['labeling_tool'],
    scripts=['bin/LabelingTool'],
    install_requires=dependencies(),
    include_package_data=True,
    cmdclass={
            'build_ui': build_ui
    }
)
