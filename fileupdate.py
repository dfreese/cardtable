import os

def updateWsAddress(filename, envvar):
    filedata = None
    with open(filename, 'r') as f:
        filedata = f.read()
    newval = os.getenv(envvar, 'localhost')
    filedata = filedata.replace(envvar, newval)
    with open(filename, 'w') as f:
        f.write(filedata)

