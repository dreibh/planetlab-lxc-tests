#!/usr/bin/python

sites = []
persons = []
slices = []

plcs = [
	{'name': 'TestPLC',
         'host': 'localhost',
         'ip': '127.0.0.1',
         'url': 'https://localhost.localdomain/',
         'port': '443'
        },
	{'name': 'ParisPLC',
	 'host': 'localhost',
	 'ip': '127.0.0.1',
	 'url': 'https://localhost.localdomain/',
	 'port': '443',
	 'chroot': '/plc/root/'
	}
	]

sites = [
	{'plc': 'ParisPLC',
	 'name': 'TestSite1',
	 'login_base': 'ts',
	 'enabled': True,
	 'abbreviated_name': 'Test1',
	 'max_slices': 100,
	 'is_public': True,
	 'url': 'http://pl-test.planet-lab.org'
	}
	]

nodes = [
	{'plc': 'ParisPLC',   	
	 'site': 'ts',
	 'hostname': 'vm1.paris.cs.princeton.edu',
	 'host': 'localhost',
	 'type': 'virtual',
	 'nodenetworks' : [{'type': 'ipv4',
			   'method': 'static',
			   'ip': '10.0.2.16',
			   'gateway': '10.0.2.2',
			   'dns1': '10.0.2.2',
			   'network': '10.0.2.0',
			   'netmask': '255.255.255.0',
			   'broadcast': '10.0.2.255'
			   }]
	}
	
	]

slices = [
	{'plc': 'ParisPLC',   
	 'name': 'ts_slice1',
	 'instantiation': 'plc-instantiated',
	 'max_nodes': 1000,
	 'description': 'blank',
	 'url': 'http://test.org',
	 'nodes': ['vm1.paris.cs.princeton.edu']
	}
	]

persons = [
	{'plc': 'ParisPLC',
	 'first_name': 'fname',
	 'last_name': 'lname',
	 'password': 'password',
	 'email': 'person@cs.princeton.edu',
	 'roles': ['user', 'pi'],
	 'sites': ['ts'], 
	 'slices': ['ts_slice1']
	}
	]
