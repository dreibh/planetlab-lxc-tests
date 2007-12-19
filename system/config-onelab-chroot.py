# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

onelab="one-lab.org"

# use a model that contains "vmware" to get the node actually started
def nodes():
    return [ {'node_fields': {'hostname': 'test1.one-lab.org',
                              'model':'vmware/minhw'},
              'owner' : 'pi',
              'network_fields': { 'method':'static',
                                  'type':'ipv4',
                                  'ip':'192.168.132.128',
                                  'gateway':'192.168.132.1',
                                  'network':'192.168.132.0',
                                  'broadcast':'192.168.132.255',
                                  'netmask':'255.255.255.0',
                                  'dns1': '192.168.132.2',
                                  },
              },
             { 'node_fields': {'hostname':'test2.one-lab.org',
                               'model':'vmware/minhw'},
               'owner' : 'tech',
               'network_fields': {'method':'static',
                                  'type':'ipv4',
                                  'ip':'192.168.132.130',
                                  'gateway':'192.168.132.1',
                                  'network':'192.168.132.0',
                                  'broadcast':'192.168.132.255',
                                  'netmask':'255.255.255.0',
                                  'dns1': '192.168.132.2',
                                  },
               },
             ]

def all_nodenames ():
    return [ node['node_fields']['hostname'] for node in nodes()]

def users (domain=onelab) :
    return [ {'name' : 'pi', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'PI', 'last_name':'PI',
                               'enabled':'True',
                               'email':'fake-pi1@%s'%domain,
                               'password':'testpi'},
              'roles':['pi']},
             {'name' : 'tech', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'Tech', 'last_name':'Tech',
                               'enabled':'true',
                               'email':'fake-tech1@%s'%domain,
                               'password':'testtech'},
              'roles':['tech']},
             {'name':'user', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'User', 'last_name':'User',
                               'enabled':'true',
                               'email':'fake-user1@%s'%domain,
                               'password':'testuser'},
              'roles':['user']},
             {'name':'techuser', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'UserTech', 'last_name':'UserTech',
                               'enabled':'true',
                               'email':'fake-tech2@%s'%domain,
                               'password':'testusertech'},
              'roles':['tech','user']},
             {'name':'pitech', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'PiTech',
                               'last_name':'PiTech',
                               'enabled':'true',
                               'email':'fake-pi2@%s'%domain,
                               'password':'testusertech'},
              'roles':['pi','tech']},
             ]

def all_usernames ():
    return [ user['name'] for user in users()]

def sites ():
    return [ {'site_fields' : {'name':'mainsite',
                               'login_base':'main',
                               'abbreviated_name':'PLanettest',
                               'max_slices':100,
                               'url':'http://onelab-test.inria.fr',
                               },
              'address_fields' : {'line1':'route des lucioles',
                                  'city':'sophia',
                                  'state':'fr',
                                  'postalcode':'06600',
                                  'country':'france',
                                  },
              'users' : users(),
              'nodes': nodes(),
            }]

def keys ():
    return [ {'name': 'key1',
              'key_fields' : {'key_type':'ssh',
                              'key':'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFUYyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXeWYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzVFN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bw== root@onelab-test.inria.fr'}}
             ]

def initscripts(): 
    return [ { 'name' : 'test1',
               'initscript_fields' : { 'enabled' : True,
                                       'name':'Test1',
                                       'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 1; date) > /tmp/initscript1.log \n ',
                                       }},
             { 'name' : 'test2',
               'initscript_fields' : { 'enabled' : True,
                                       'name':'Test2',
                                       'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 2; date) > /tmp/initscript2.log \n ',
                                       }},
             ]

def slices ():
    both = [ { 'slice_fields': {'name':'main_slicetest1',
                                'instantiation':'plc-instantiated',
                                'url':'http://foo@ffo.com',
                                'description':'testslice the first slice for the site testsite',
                                'max_nodes':2
                                },
               'usernames' : [ 'pi','tech','techuser' ],
               'nodenames' : all_nodenames(),
               'initscriptname' : 'test1',
               'sitename' : 'main',
               'owner' : 'pi',
               },
             { 'slice_fields': {'name':'main_slicetest2',
                                'instantiation':'plc-instantiated',
                                'url':'http://foo2@ffo2.com',
                                'description':'testslice the second slice for the site testsite',
                                'max_nodes':100
                                },
               'usernames' : [ 'user', 'pitech' ],
               'nodenames' : all_nodenames(),
               'initscriptname' : 'test2',
               'sitename' : 'main',
               'owner' : 'pi',
               }]
    # I suspect the check_slices stuff to work improperly with 2 slices
    return both

def plc () :
    return { 
        'name' : 'onelab-chroot',
        # as of yet, not sure we can handle foreign hosts, but this is required though
        'hostname' : 'localhost',
        # use this to run in a vserver
        # 'vserver': '138.96.250.131'
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
        'sites' : sites(),
        'keys' : keys(),
        'initscripts': initscripts(),
        'slices' : slices(),
    }

def config (plc_specs,options):
    return plc_specs + [ plc() ]

