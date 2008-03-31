# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# values like 'hostname', 'ip' and the like my be rewritten later with a TestPool object

def nodes(options):
    nodes= [{'name':'node1',
             'node_fields': {'hostname': 'deferred01',
                             'model':'qemu/minhw', } ,
             'host_box': 'testbox1.one-lab.org',
             'owner' : 'pi',
             'network_fields': { 'method':'static',
                                 'type':'ipv4',
                                 'ip':'xx-deferred-xxx',
                                 'gateway':'xx-deferred-xxx',
                                 'network':'xx-deferred-xxx',
                                 'broadcast':'xx-deferred-xxx',
                                 'netmask':'xx-deferred-xxx',
                                 'dns1': 'xx-deferred-xxx',
                                 'dns2': 'xx-deferred-xxx',
                                 },
             },
            {'name':'node2',
             'node_fields': {'hostname': 'deferred02',
                             'model':'qemu/minhw', } ,
             'host_box': 'testbox1.one-lab.org',
             'owner' : 'pi',
             'network_fields': { 'method':'static',
                                 'type':'ipv4',
                                 'ip':'xx-deferred-xxx',
                                 'gateway':'xx-deferred-xxx',
                                 'network':'xx-deferred-xxx',
                                 'broadcast':'xx-deferred-xxx',
                                 'netmask':'xx-deferred-xxx',
                                 'dns1': 'xx-deferred-xxx',
                                 'dns2': 'xx-deferred-xxx',
                                 },
             },
            ]
    if options.small_test:
        return [nodes[0]]
    else:
        return nodes

def all_nodenames (options):
    return [ node['name'] for node in nodes(options)]

def users (options) :
    domain="one-lab.org"
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

def all_usernames (options):
    return [ user['name'] for user in users(options)]

def sites (options):
    return [ {'site_fields' : {'name':'mainsite',
                               'login_base':'main',
                               'abbreviated_name':'PLanettest',
                               'max_slices':100,
                               'url':'http://testbox1.one-lab.org',
                               },
              'address_fields' : {'line1':'route des lucioles',
                                  'city':'sophia',
                                  'state':'fr',
                                  'postalcode':'06600',
                                  'country':'france',
                                  },
              'users' : users(options),
              'nodes': nodes(options),
            }]

##########
public_key="""ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFUYyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXeWYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzVFN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bw== root@test.one-lab.org
"""
private_key="""-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFU
YyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXe
WYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp
9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzV
FN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO
+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bwIBIwKCAQATY32Yf4NyN93oNd/t
QIyTuzG0NuLI3W95J/4gI4PAnUDmv6glwRiRO92ynlnnAjqFW/LZ5sGFd4k8YoYU
sjaa8JJgpwrJBi9y6Fx47/9Tp+ITPqyoliyTXvtqysX0jkaY+I1mNHoTITDkbknZ
eTma0UOhiKcrMz4qOMwg+kajWsAhIplJXyf0Mio/XuyqjMT4wI/NyGZQ4bGuUjO7
gj3p+9psOvONsRBW4MV27W5ts9c7HEXg+VJ2PSCEMs+uyzXcdnMJcTb4zQ/+tVxR
5IMeEuR9ZzDNkDtNF6Nnw5kYcTBNoayzZbUfjcuSmsMklMXr0qJ4qcW9/ONKgBQ9
6qhDAoGBAPkvSYuF/bxwatEiUKyF97oGDe025h/58aqK1VBD5/BBVqqvbQOeNtR5
/LerGfFa5D9Jm+6U97gDdq3tH0j95Mo0F00LWq2+vp7U4DTQsiddepzNdbcvSrzT
NVZ2cnOAlKTHO4hGggShm04n/M5LOzkHtI5TLcIJjw4b5iiIw9EtAoGBAOhjLTds
Zz8UbXVTeGv8yBGhnjAeHQ5WISN6V5KenB4GIyaYCCcQUOUGqc5nCttlnPLv/GHp
4DOJ2/0KbwDEwk7HbAtXG2Tv1OkmfcOq9RH19V9lyqynA+zvI6taisCEaMvBlafd
k+RgXsR+NdLs96RakKt4BtgpuuADoSIryQ+LAoGBAKremNSzpq0Z4tiMjxc3Ssiz
scc7lnxTnmZQkkWq6C+3xmZpqdaYYByra3ahNlxblTK2IcgroozPLM8I/4KCNnwG
dmC3VB9eOZF8B3SsXOfLEj+i1GBa8WuJg6kAw4JmzFO70Qz9JfSMErk//c9Jh7IT
6YYqaIUN3nATIXrhcFTrAoGAVlC5BfUQZ+MEFaKpEiqwthd1RRJ/0h/9rhd/nNvT
lh+JZhs2OmUlXGGPhy2WUX2DcC1AfCOrC9Qego7YxcVsvizQW/vIWLDaDXSyXp6V
ilQKrmejDO2Tvmdzpguv4Rs83fdyGcdUMEENQas4kCwhd49aTlEnHRbQYdV2XSY0
vKECgYEAlhYzfSswIF2h5/hGDLETxgNJ2kD0HIZYh7aud6X6aEYNdJopbfbEhifU
vTbf8GtvERDoxWEsk9Qp7km8xXfKWdcZtqIwsSmn/ri5d7iyvpIk591YIHSY0dr2
BO+VyPNWF+kDNI8mSUwi7jLW6liMdhNOmDaSX0+0X8CHtK898xM=
-----END RSA PRIVATE KEY-----
"""

def keys (options):
    return [ {'name': 'key1',
              'private' : private_key,
              'key_fields' : {'key_type':'ssh',
                              'key': public_key}}
             ]

def initscripts(options): 
    initscripts= [ { 'initscript_fields' : { 'enabled' : True,
                                             'name':'script1',
                                             'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 1; date) > /tmp/initscript1.log \n ',
                                             }},
                   { 'initscript_fields' : { 'enabled' : True,
                                             'name':'script2',
                                             'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 2; date) > /tmp/initscript2.log \n ',
                                             }},
                   ]
    if options.small_test:
        return [initscripts[0]]
    else:
        return initscripts

def slices (options):
    both = [ { 'slice_fields': {'name':'main_slicetest1',
                                'instantiation':'plc-instantiated',
                                'url':'http://foo@ffo.com',
                                'description':'testslice the first slice for the site testsite',
                                'max_nodes':2
                                },
               'usernames' : [ 'pi','tech','techuser' ],
               'nodenames' : all_nodenames(options),
               'initscriptname' : 'script1',
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
               'nodenames' : all_nodenames(options),
               'initscriptname' : 'script2',
               'sitename' : 'main',
               'owner' : 'pi',
               }]
    if options.small_test:
        return [both[0]]
    else:
        return both


def all_slicenames (options):
    return [ slice['slice_fields']['name'] for slice in slices(options)]

def tcp_param (options):
    try:
        return [{ 'tcp_fields' :  {'peer_name' : 'server',
                                   'slice_name' :all_slicenames(options)[0],
                                   'server_name': all_nodenames()[0]
                                   },
                  
                  },
                { 'tcp_fields':{'peer_name' : 'client',
                                'slice_name' :all_slicenames()[1],
                                'client_name': all_nodenames()[1],
                                'peer_server' :  all_nodenames()[0],
                                'server_port' : 22
                                },
                  },
                
                ]
    except:
        return None

def plc (options) :
    return { 
        'name' : 'onetest',
        # as of yet, not sure we can handle foreign hosts, but this is required though
        'hostname' : 'xx-deferred-xxx',
        # set these two items to run within a vserver
        # 'vservername': '138.96.250.131'
        # 'vserverip': '138.96.250.131'
        'role' : 'root',
        'PLC_ROOT_USER' : 'root@test.one-lab.org',
        'PLC_ROOT_PASSWORD' : 'test++',
        'PLC_NAME' : 'TestLab',
        'PLC_MAIL_ENABLED':'true',
        'PLC_MAIL_SUPPORT_ADDRESS' : 'mohamed-amine.chaoui@sophia.inria.fr',
        'PLC_DB_HOST' : 'test.one-lab.org',
        'PLC_API_HOST' : 'test.one-lab.org',
        'PLC_WWW_HOST' : 'test.one-lab.org',
        'PLC_BOOT_HOST' : 'test.one-lab.org',
        'PLC_NET_DNS1' : 'xx-deferred-xxx',
        'PLC_NET_DNS2' : 'xx-deferred-xxx',
        'sites' : sites(options),
        'keys' : keys(options),
        'initscripts': initscripts(options),
        'slices' : slices(options),
        'tcp_param' : tcp_param(options),
    }

def config (plc_specs,options):
    return plc_specs + [ plc(options) ]