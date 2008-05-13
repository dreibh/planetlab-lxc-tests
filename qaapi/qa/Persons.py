import os
from Table import Table

class Person(dict):

     fields = {
	'plcs': ['TestPLC'],
	'first_name': None,
	'last_name': None,
	'password': None,
	'email': None,
	}

     def __init__(self, fields = {}):

	dict.__init__(self, self.fields)
	
	self.update(fields)

class Persons(Table):
    def __init__(self, persons):
	personlist = [Person(person) for person in persons]
	Table.__init__(self, personlist)				 	  			 	 	
