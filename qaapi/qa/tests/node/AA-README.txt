All scripts in this directory that
- start with a letter
- end with .pl .py or .sh
get triggered in the root context of a test node as part of the system/ test suite

As far as possible, would you please 
- pick up a meaningful name
- and provide a corresponding .help file

===
The list of extensions that are considered (.pl .py or .sh) is defined
in system/TestNode.py

If for any reason a given script needs to be turned off, it is
recommended to simply svn rename it and add '.hide' to its name
