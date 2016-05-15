# average_degree.py

# Coding Challenge (31 Mar 2016)
# For Insight Data Engineering Application
# Kendrick Lo
# Details at: https://github.com/ppgmg/coding-challenge

import sys
import graph

inputfile = sys.argv[1]
outputfile = sys.argv[2]

g = graph.Graph()

with open(inputfile) as f1:
    with open(outputfile, "a") as f2:  # note, write appends to existing file
        for i, line in enumerate(f1):
            avg = g.process_tweet(line, log=False)
            if avg is not None:
                s = "%.2f\n" % avg  # truncate to 2 decimal places here
                f2.writelines(s)
