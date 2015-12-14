'''Script to fill csvdb database with example data.'''

import random
import os
from subprocess import Popen

cmd = 'sqlite3 csvdb "%s" '


def e(stmt):
    p = Popen( cmd % stmt, shell=True)
    os.waitpid(p.pid, 0)

e("CREATE TABLE experiment1_data "
  "(gene_id TEXT, function TEXT, expression INT)")

for x in range(0, 200, 2):
    e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" %
       ("experiment1_data", x, "housekeeping", random.gauss(41, 5)))
    e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" %
       ("experiment1_data", x+1, "regulation", random.gauss(11, 5)))

e("CREATE TABLE experiment2_data "
  "(gene_id TEXT, function TEXT, expression INT)")

for x in range(0, 200, 2):
    e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" %
       ("experiment2_data", x, "housekeeping", random.gauss(40, 5)))
    e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" %
       ("experiment2_data", x+1, "regulation", random.gauss(10, 5)))


