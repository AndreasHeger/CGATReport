'''Configuration values in SphinxReport.

This module sets some default variables and
neads the sphinx conf.py file.
'''

import os

SEPARATOR="@"

HTML_IMAGE_FORMAT = ('main', 'png', 80)
LATEX_IMAGE_FORMAT = () # ('pdf', 'pdf' 50)

ADDITIONAL_FORMATS = [
    ('hires', 'hires.png', 200),
    # ('eps', 'eps', 50),
    # ('svg', 'svg', 50),
    # ('pdf', 'pdf', 50),
    ]

# import conf.py
if os.path.exists("conf.py"):
    try:
        exec(compile(open("conf.py").read(), "conf.py", 'exec'))
    except ValueError:
        pass


