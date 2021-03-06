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
	 'host': 'paris.cs.princeton.edu',
	 'ip': '128.112.95.151',
	 'url': 'https://paris.cs.princeton.edu/',
	 'port': '443',
	 'chroot': '/plc/root/'
	}
	]

sites = [
	{'plcs': ['TestPLC', 'ParisPLC'],
	 'name': 'TestSite1',
	 'login_base': 'ts',
	 'enabled': True,
	 'abbreviated_name': 'Test1',
	 'max_slices': 100,
	 'is_public': True,
	 'url': 'http://pl-test.planet-lab.org'
	}
	]

#nodegroups = [
#	{'plcs': ['TestPLC', 'ParisPLC'],
#	 'name': '41',	 
#	 'nodes': ['vm41.test.org'],
#	}
#	]
	 
nodes = [
	{'plcs': ['TestPLC', 'ParisPLC'],   	
	 'site': 'ts',
	 'hostname': 'vm1.paris.cs.princeton.edu',
	 'host': 'localhost',
	 'redir_ssh_port': '51022',
	 'type': 'vm',
	 'model' : 'qemu/minhw',
	 'boot_state': 'rins', 
	 'nodenetworks' : [{'type': 'ipv4',
			   'method': 'static',
			   'ip': '10.0.2.16',
			   'gateway': '10.0.2.2',
			   'dns1': '10.0.2.3',
			   'network': '10.0.2.0',
			   'netmask': '255.255.255.0',
			   'broadcast': '10.0.2.255',
			   'mac': u'52:54:00:12:34:56'
			   }]
	},
	{'plcs': ['TestPLC', 'ParisPLC'],
	 'site': 'ts',
	 'hostname': 'vm41.test.org',
	 'host': 'localhost',
	 'redir_ssh_port': '51122',
	 'type': 'vm',
	 'model': 'qemu/minhw',
	 'boot_state': 'rins',
	 #'nodegroups': ['41'],	
	 'nodenetworks': [{'type': 'ipv4',
			   'method': 'static',
	  	   	   'ip': '10.0.2.17',
			   'gateway': '10.0.2.2',
                           'dns1': '10.0.2.3',
                           'network': '10.0.2.0',
                           'netmask': '255.255.255.0',
                           'broadcast': '10.0.2.255',
                           'mac': u'52:54:00:12:34:56'
			   }]	 			 	
	}
	]

slices = [
	{'plcs': ['TestPLC','ParisPLC'],   
	 'name': 'ts_slice1',
	 'instantiation': 'plc-instantiated',
	 'max_nodes': 1000,
	 'description': 'blank',
	 'url': 'http://test.org',
	 'nodes': ['vm1.paris.cs.princeton.edu', 'vm41.test.org'],
	 'persons': ['person@cs.princeton.edu']	
	}
	]

persons = [
	{'plc': ['TestPLC', 'ParisPLC'],
	 'first_name': 'fname',
	 'last_name': 'lname',
	 'password': 'password',
	 'email': 'person@cs.princeton.edu',
	 'roles': ['user', 'pi'],
	 'sites': ['ts'], 
	 'slices': ['ts_slice1']
	}
	]
