import os
from datetime import datetime, timezone
import yaml

class BaseLogger:
    def __init__(self) -> None:
        self.info = print

#Writes the selected addition to a .md file. Not presently in use
def write_to_md(addition):
    print(addition)
    with open(f"{os.getcwd()}/output.md", "w") as f:
        f.write(addition)
        f.close()


# for checking if an attribute of the state dict has content.

def check_for_content(var):
    if var:
        if type(var)==list:
            var=var[-1]
        try:
            var = var.content
            return var.content
        except:
            
            return var
    else:
        var

