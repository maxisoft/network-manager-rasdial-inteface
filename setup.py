from cx_Freeze import setup, Executable

includefiles = []
includes = ['imp', 'importlib']
excludes = []
packages = []
filename = "rasdial.py"
setup(
    name='rasdial',
    version='0.1',
    description='rasdial like interface',
    author='maxisoft',
    options={'build_exe': {'excludes': excludes, 'packages': packages, 'include_files': includefiles}},
    executables=[Executable(filename, base=None, icon=None)])