# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# archs & vrefs :
# current focus is to
########## myplc
# (*) run a 32bits myplc
########## multi-arch
# (*) run wlab02 as a plain 32bits node
# (*) try and run 64bits in wlab17 (i.e. bootcd & bootstrapfs)
#     which should be achieved by simply adding this node in the 'x86_64' nodegroup
# (*) investigate what it takes to have the slivers on wlab17 run 32bits as well
########## multi-vref
# (*) define slice 'plain' without secific tuning, that should result in f8-based slivers
# (*) define slice 'centos' with its vref set to centos5
########## manual stuff
# all this would require to
# (*) install bootcd            f8-x86_64
# (*) install bootstrapfs       f8-x86_64
# (*) install noderepo          f8-x86_64 
# (*) install noderepo          centos5-i386
# (*) install noderepo          centos5-x86_64
# (*) install vserver           centos5-i386
# (*) and add that to yumgroups.xml
########## unclear stuff
# I'm pretty sure that yum.conf.php still needs hacking, at least for centos5
########## unclear stuff

onelab="onelab.eu"

# these are real nodes, they dont get started by the framework
def nodes():
    node02 = {'name':'wlab02',
              'node_fields': {'hostname': 'wlab02.inria.fr', 'model':'Dell Latitude 830'},
              'owner' : 'pi',
              'nodegroups' : 'wifi',
              'interface_fields': { 'method':'dhcp', 'type' : 'ipv4', 'ip':'138.96.250.162',},
              'extra_interfaces' : [ { 'interface_fields' : { 'method' : 'dhcp',
                                                            'type' : 'ipv4',
                                                            'mac' : '00:1B:77:70:F4:C6',
                                                            'ip' : '138.96.250.192', },
                                       'settings' : { 'essid' : 'guest-inria-sophia',
                                                      'ifname' : 'wlan0', },
                                       },
                                     ],
              }
    node17 = {'name':'wlab17',
              'node_fields': {'hostname': 'wlab17.inria.fr', 'model':'Dell Latitude 830'},
              'owner' : 'pi',
              'nodegroups' : ['wifi','x86_64'] ,
              'interface_fields': { 'method':'dhcp', 'type' : 'ipv4', 'ip':'138.96.250.177',},
              'extra_interfaces' : [ { 'interface_fields' : { 'method' : 'dhcp',
                                                            'type' : 'ipv4',
                                                            'mac' : '00:1c:bf:51:3c:19',
                                                            'ip' : '138.96.250.207',},
                                       'settings' : { 'essid' : 'guest-inria-sophia',
                                                      'ifname' : 'wlan0',},
                                       },
                                     ],
              }
    node05 = {'name':'wlab05',
              'node_fields': {'hostname': 'wlab05.inria.fr', 'model':'Dell Latitude 830'},
              'owner' : 'pi',
              'nodegroups' : 'wifi',
              'interface_fields': { 'method':'dhcp', 'type' : 'ipv4', 'ip':'138.96.250.165',},
              'extra_interfaces' : [ { 'interface_fields' : { 'method' : 'static',
                                                            'type' : 'ipv4',
                                                            'mac' : '00:1B:77:70:FC:84',
                                                            'ip' : '138.96.250.215',
                                                            'network' : '138.96.0.0',
                                                            'dns1': '138.96.0.10',
                                                            'dns2': '138.96.0.11',
                                                            'broadcast' : '138.96.255.255',
                                                            'netmask' : '255.255.0.0',
                                                            'gateway' : '138.96.248.250',},
                                       'settings' : { 'essid' : 'guest-inria-sophia',
                                                      'ifname' : 'wlan0',},
                                       },
                                     { 'interface_fields' : { 'method' : 'dhcp',
                                                            'type' : 'ipv4',
                                                            'mac' : '00:20:A6:4E:FF:E6',
                                                            'ip' : '138.96.250.50',
                                                            'hostname' : 'radio40.inria.fr', },
                                       'settings' : { 'essid' : 'guest-inria-sophia',
                                                      'ifname' : 'wifi0',},
                                       },
                                     ],
              }


    # wlab05 not avail. for now
    return [ node02 , node17 ]

def all_nodenames ():
    return [ node['name'] for node in nodes()]

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
    return [ {'site_fields' : {'name':'wifisite',
                               'login_base':'wifi',
                               'abbreviated_name':'wifi',
                               'max_slices':100,
                               'url':'http://test.onelab.eu',
                               },
              'address_fields' : {'line1':'route des lucioles',
                                  'city':'sophia',
                                  'state':'fr',
                                  'postalcode':'06902',
                                  'country':'france',
                                  },
              'users' : users(),
              'nodes': nodes(),
            }]

##########
public_key="""ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFUYyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXeWYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzVFN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bw== root@test.onelab.eu
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

def keys ():
    return [ {'name': 'key1',
              'private' : private_key,
              'key_fields' : {'key_type':'ssh',
                              'key': public_key}}
             ]

def initscripts(): 
    return [ { 'initscript_fields' : { 'enabled' : True,
                                       'name':'script_plain',
                                       'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 1; date) > /tmp/initscript_plain.log \n ',
                                       }},
             { 'initscript_fields' : { 'enabled' : True,
                                       'name':'script_centos',
                                       'script' : '#! /bin/sh\n (echo Starting test initscript: Stage 2; date) > /tmp/initscript_centos.log \n ',
                                       }},
             ]

def slices ():
    plain= { 'slice_fields': {'name':'wifi_plain',
                                'instantiation':'plc-instantiated',
                                'url':'http://foo@foo.com',
                                'description':'plain slice',
                                'max_nodes':10,
                                },
               'usernames' : [ 'pi','tech','techuser' ],
               'nodenames' : all_nodenames(),
               'initscriptname' : 'script_plain',
               'sitename' : 'wifi',
               'owner' : 'pi',
               }
    centos= { 'slice_fields': {'name':'wifi_centos',
                                'instantiation':'plc-instantiated',
                                'url':'http://foo@foo.com',
                                'description':'centos slice',
                                'max_nodes':10,
                                },
               'usernames' : [ 'pi','tech','techuser' ],
               'nodenames' : all_nodenames(),
               'initscriptname' : 'script_centos',
               'sitename' : 'wifi',
               'owner' : 'pi',
              'vref' : 'centos5',
               }
             ]

def plc () :
    return { 
        'name' : 'wifilab',
        # as of yet, not sure we can handle foreign hosts, but this is required though
        'hostname' : 'wlab24.inria.fr',
        # set these two items to run within a vserver
        # 'vservername': 'somename'
        # 'vserverip': '138.96.250.131'
        'role' : 'root',
        'PLC_ROOT_USER' : 'root@wlab24.inria.fr',
        'PLC_ROOT_PASSWORD' : 'test++',
        'PLC_NAME' : 'WifiLab',
        'PLC_MAIL_ENABLED':'true',
        'PLC_MAIL_SUPPORT_ADDRESS' : 'thierry.parmentelat@sophia.inria.fr',
        'PLC_DB_HOST' : 'wlab24.inria.fr',
        'PLC_API_HOST' : 'wlab24.inria.fr',
        'PLC_WWW_HOST' : 'wlab24.inria.fr',
        'PLC_BOOT_HOST' : 'wlab24.inria.fr',
        'PLC_NET_DNS1' : '138.96.0.10',
        'PLC_NET_DNS2' : '138.96.0.11',
        'PLC_DNS_ENABLED' : 'false',
        'sites' : sites(),
        'keys' : keys(),
        'initscripts': initscripts(),
        'slices' : slices(),
    }

def config (plc_specs,options):
    return plc_specs + [ plc() ]
