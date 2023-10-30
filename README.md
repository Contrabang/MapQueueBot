# MapQueueBot
Automatic bot for making a graph of a Map Queue on github.

Primarily based around the ParadiseSS13/Paradise repository.

# How to install

Install a few packages, everything else should work right out of the box.
```
pip install networkx
pip install requests
pip install matplotlib
```

# How to use
Use the "help" command when prompted.

the "run" command will automatically download all data from the github, isolate them down to the map PRs, and then make an output in the output folder.
If your repo has more than 100 PRs, you will be prompted in the command line whether you would like to continue downloading PRs.
