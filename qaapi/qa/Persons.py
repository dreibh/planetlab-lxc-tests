import os
from Table import Table

class Person(dict):

     fields = {
	'plc': None,
	'first_name': None,
	'last_name': None,
	'password': None,
	'email': None,
	}

     def __init__(self, fields = {}):

	dict.__init__(self, self.fields)
	
	self.update(fields)

class Persons(list, Table):
    def __init__(self, persons):
	personlist = [Person(person) for person in persons]
	list.__init__(self, personlist)				 	  			 	 	
