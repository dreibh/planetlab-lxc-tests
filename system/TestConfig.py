#definition of all structure used by the test_setup.py script
site1_nodes = {
'node1' :  {'hostname': 'test1.one-lab.org',
            'boot_state':'inst',
            'model':'vmware/minhw',
            'owned' : 'pi',
            'network': { 'method':'static',
                         'type':'ipv4',
                         'ip':'192.168.132.128',
                         'gateway':'192.168.132.1',
                         'network':'192.168.132.0',
                         'broadcast':'192.168.132.255',
                         'netmask':'255.255.255.0',
                         'dns1': '192.168.132.2',
                         },
            
            },
'node2' :   { 'hostname':'test2.one-lab.org',
              'boot_state':'inst',
              'model':'vmware/minhw',
              'owned' : 'tech',
              'network': {'method':'static',
                          'type':'ipv4',
                          'ip':'192.168.132.130',
                          'gateway':'192.168.132.1',
                          'network':'192.168.132.0',
                          'broadcast':'192.168.132.255',
                          'netmask':'255.255.255.0',
                          'dns1': '192.168.132.2',
                          },
              
              },
}
site_users= {
'pi_spec' : {'first_name':'PI',
	       'last_name':'PI',
	       'enabled':'True',
	       'email':'fake-pi1@one-lab.org',
	       'password':'testpi',
	       'roles':['pi'],
               'auth_meth':'pi',
	       },
'tech_spec' : {'first_name':'Tech',
               'last_name':'Tech',
		 'enabled':'true',
		 'email':'fake-tech1@one-lab.org',
		 'password':'testtech',
		 'roles':['tech'],
                 'auth_meth':'tech',
		 },
'user_spec' : {'first_name':'User',
		 'last_name':'User',
		 'enabled':'true',
		 'email':'fake-user1@one-lab.org',
		 'password':'testuser',
		 'roles':['user'],
                 'auth_meth':'user',
		 },
'tech_user_spec' : {'first_name':'UserTech',
		 'last_name':'UserTech',
		 'enabled':'true',
		 'email':'fake-tech2@one-lab.org',
		 'password':'testusertech',
		 'roles':['tech','user'],
                 'auth_meth':'techuser',
                 },
'pi_tech_spec' : {'first_name':'PiTech',
		 'last_name':'PiTech',
		 'enabled':'true',
		 'email':'fake-pi2@one-lab.org',
		 'password':'testusertech',
		 'roles':['pi','tech'],
                 'auth_meth':'pitech',
                  },
}
site_spec1 = {
'site_fields' : {'name':'testsite',
		 'login_base':'ts',
		 'abbreviated_name':'PLanettest',
		 'max_slices':100,
		 'url':'http://onelab-test.inria.fr',
		 },
'site_address' : {'line1':'route des lucioles',
		  'city':'sophia',
		  'state':'fr',
		  'postalcode':'06600',
		  'country':'france',
		  },
'users': [ site_users['pi_spec'], site_users['tech_spec'], site_users['user_spec'],site_users['tech_user_spec'],site_users['pi_tech_spec']],
'nodes' :  [ site1_nodes['node1'], site1_nodes['node2']],
}

    
site_specs = [ site_spec1 ]

plc_spec1 =  { 
    'hostname' : 'localhost',
    'role' : 'root',
    'PLC_ROOT_USER' : 'root@onelab-test.inria.fr',
    'PLC_ROOT_PASSWORD' : 'test++',
    'PLC_NAME' : 'TestLab',
    'PLC_MAIL_ENABLED':'true',
    'PLC_MAIL_SUPPORT_ADDRESS' : 'mohamed-amine.chaoui@sophia.inria.fr',
    'PLC_DB_HOST' : 'onelab-test.inria.fr',
    'PLC_API_HOST' : 'onelab-test.inria.fr',
    'PLC_WWW_HOST' : 'onelab-test.inria.fr',
    'PLC_BOOT_HOST' : 'onelab-test.inria.fr',
    'PLC_NET_DNS1' : '138.96.0.10',
    'PLC_NET_DNS2' : '138.96.0.11',
    'sites' : site_specs,
    }
plc_specs = [ plc_spec1 ]

key={'key_type':'ssh',
     'key':'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFUYyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXeWYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzVFN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bw== root@onelab-test.inria.fr'}


slice1_spec={
'slice_spec':{'name':'ts_slicetest1',
              'instantiation':'plc-instantiated',
              'url':'http://foo@ffo.com',
              'description':'testslice the first slice for the site testsite',
              'max_nodes':1000
              },
'slice_users' : [ site_users['pi_spec'], site_users['tech_spec'],site_users['tech_user_spec']],
'slice_nodes' : [ site1_nodes['node1'], site1_nodes['node2'] ],
}
slices_specs= [slice1_spec]



