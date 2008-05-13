import utils
from Table import Table

class TestScript(dict):

    fields = {
	'name': None,
	'pre': None,
	'args': None,
	'post': None
	}

    def __init__(self, fields = {}):
	dict.__init__(self, self.fields)
	self.update(fields)

class TestScripts(Table):
    def __init__(self, scripts):
	scriptlist = [Script(script) for script in scripts]
	Table.__init__(self, scriptlist)    
	 
