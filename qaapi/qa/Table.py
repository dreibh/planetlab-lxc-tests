
class Table(list):
    def __init__(self, elements):
	list.__init__(self, elements)
	
    def dict(self, key_field):
 	"""
	Return ourself as a dict keyed on key_fields
	"""
	return dict([(obj[key_field], obj) for obj in self])	 
