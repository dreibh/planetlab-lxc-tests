# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# values like 'hostname', 'ip' and the like are rewritten later with a TestPool object

domain="onelab.eu"

### for the sfa dual setup
def login_base (index): 
    if index==1: return 'inri'
    elif index==2: return 'princ'
    # index=3=>'sitea'  4=>'siteb' 
    else: return 'site%s'%chr(index+94)

def sfa_login_base (index, rspec_style):
    return "sfa%s"%(rspec_style)

def sfa_root (index):
    # use plt (planetlab test) instead of pl
    # otherwise a triangular test ends up with 'plc'
    # plta, pltb, ...
    return 'plt%s'%chr(index+96)

def nodes(options,index):
    return [{'name':'node%d'%index,
             'node_fields':             {'hostname': 'deferred-nodename%d'%index,
                                         'model':'qemu/minhw', } ,
             'host_box': 'deferred-node-hostbox-%d'%index,
             'owner' : 'pi',
             'nodegroups' : 'mynodegroup',
             'interface_fields':        { 'method':'static',
                                          'type':'ipv4',
                                          'ip':'xxx-deferred-xxx',
                                          'gateway':'xxx-deferred-xxx',
                                          'network':'xxx-deferred-xxx',
                                          'broadcast':'xxx-deferred-xxx',
                                          'netmask':'xxx-deferred-xxx',
                                          'dns1': 'xxx-deferred-xxx',
                                          'dns2': 'xxx-deferred-xxx',
                                          },
             ######## how to deal with the new plcapi way of modeling interfaces
             # this pertains to the node as per the new interface - using UpdateNode
             # after node_fields above is used to create the Node
             'node_fields_nint' :       { 'dns':'xxx-deferred-xxx',
                                          },
             # used in replacement of interface_fields above
             'interface_fields_nint' :  { 'is_primary' : True,
                                          'method' : 'static',
                                          },
             # used to create an IpAddress
             'ipaddress_fields' :       { 'type' : 'ipv4',
                                          'ip_addr' : 'xxx-deferred-xxx',
                                          'netmask' : 'xxx-deferred-xxx',
                                          } ,
             # used to create a Route
             'route_fields' :           { 'subnet' : '0.0.0.0/0',
                                          'next_hop' : 'xxx-deferred-xxx',
                                          },
             }]

def all_nodenames (options,index):
    return [ node['name'] for node in nodes(options,index)]

def users (options) :
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
             {'name':'admin', 'keynames' : [ 'key1' ],
              'user_fields' : {'first_name':'Admin',
                               'last_name':'Admin',
                               'enabled':'true',
                               'email':'admin@%s'%domain,
                               'password':'testuseradmin'},
              'roles':['admin']},
             ]

def all_usernames (options):
    return [ user['name'] for user in users(options)]

def sites (options,index):
    latitude= -90 + (index*10)
    longitude= -180 + (index*20)
    return [ {'site_fields' : {'name':'main site for plc number %d'%index,
                               'login_base':login_base(index),
                               'abbreviated_name':'PlanetTest%d'%index,
                               'max_slices':100,
                               'url':'http://test.onelab.eu',
                               'latitude':float(latitude),
                               'longitude':float(longitude),
                               },
              'address_fields' : {'line1':'route des lucioles',
                                  'city':'sophia',
                                  'state':'fr',
                                  'postalcode':'06600',
                                  'country':'France',
                                  },
              'users' : users(options),
              'nodes': nodes(options,index),
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

### another keypair for the SFA user
public_key2="""ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQLvh5LkrjyLIr9UJznTJHMnqjdqzRdc9ekVmI9bx/5X4flnGtPBsr6bK/CPXmWjS2Vw0QOxi1NM45qkQJZXxroS0aehCCrvJRHgp/LOZykWCyNKqVopq9w0kH4jw1KFGIuwWROpOcMq2d/kAwyr6RV/W66KNVqu2XDiNOPJLcuZCuKrH++q3fPyP2zHSJ/irew7vwqIXbDSnVvvyRXYgc9KlR57L4BWthXcUofHlje8wKq7nWBQIUslYtJDryJg5tBvJIFfCFGmWZy0WJlGJd+yppI5jRvt9c6n9HyJKN22lUBTaTaDFvo+Xu5GEazLKG/v8h/o5WpxrrE6Y3TKeX user@test.onelab.eu
"""

private_key2="""
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0C74eS5K48iyK/VCc50yRzJ6o3as0XXPXpFZiPW8f+V+H5Zx
rTwbK+myvwj15lo0tlcNEDsYtTTOOapECWV8a6EtGnoQgq7yUR4KfyzmcpFgsjSq
laKavcNJB+I8NShRiLsFkTqTnDKtnf5AMMq+kVf1uuijVartlw4jTjyS3LmQriqx
/vqt3z8j9sx0if4q3sO78KiF2w0p1b78kV2IHPSpUeey+AVrYV3FKHx5Y3vMCqu5
1gUCFLJWLSQ68iYObQbySBXwhRplmctFiZRiXfsqaSOY0b7fXOp/R8iSjdtpVAU2
k2gxb6Pl7uRhGsyyhv7/If6OVqca6xOmN0ynlwIDAQABAoIBADZnwAmzPmEO5vkz
7DzYnPYcTA6CCiHnPt1A8Pwo9C0cZXyNzYFvTs6IEW15QwIDGvl4AHL4brmUZjyN
saAfBIgAJBBiTARLAgqO5kFcE5FnSrTnrJjUWMo0ydYkmoVt1vj7nzXX8BGG8PZ0
JoRZx7mmGhLRjzXpKJQsXq+ohtzlrSoOzkx9jKqCOerhsZGBAIMl/w+gfePWoU6q
Q/NPHM0ckgvzNRs7x+AMcCtIn+xZIBzbLTKpoEI3dIvMf46ghAG5mTc08OJjqHaS
faTUyp828teAVLtWxAAv2JKcplEnjsDNU8KOGIFkUkwLNTTvwc0pCVYwyDKVxtl3
Hv76T5ECgYEA6wiun6IHfY5a4Wcn+vrUsrt3atikiBMiXvZk7ZmU5HKc72+c4mVh
frmwF8F355ncI3w63/3CKfP+X4yvsHoR+ps27t2hMMfGco7j3bMDHHpo9n04/1ZX
pYP2RlPz4EKAhD2Wi0sgTsxchwrL42qkuolmzT4TWN32xjF2ZwhCDh8CgYEA4sEf
VY+jVrMNHoHG/v1UN8nBzF5g6PwHtoo4GrFd4pMb9wo6LX4ib4FGRQfSjZ4kQ0KB
Qxrl7xLw4GlYKnYqAqgZ1peb7JN7k5Yq1Drqi61ZZxvdQ2BbO7dx22Bb3VwsKA97
DUcWUdKLVw2gU7beMYYBNMliw/E5Gx12Mqvnx4kCgYEAyQSf9cArD+PVLrt/olUt
3cAgnq2z6v4Sg43RPLYCdnDgcJjRYYC8JhrC1U6PMvKRKXhzEmiCzEb25Nn62cFN
5z0heqLr3kC/JfO4SEF3A8BeTZNEUH6Ub+exluzuxHucV34lZ/VVKI/5Azbksxje
0vv5hMj22ybcjR542h5iAJkCgYAsFw8HrPk+l2wanXNbC1j/y/whx8wiITdCuBd2
oTw3HRGX9GYhiGAbvFA0hfPb038LkPffW3CQDufFStZ40ycSAyua/Tm1Q2wI428K
ezY12IwEr3dTbX3v25iI5nCWVyDC3Ve42jStzjmHwL+G54zGpl6/q9THcrT+37im
26QiuQKBgQCTUDGKLqQ+QM8dAl6IZpz+oExdDCWwCNjTMH83tz1Rwoc+npW7z2ZC
D/FseVOmS9MqJkgCap5pr4m1Qj5YciZNteIHdkIbD1yDoPaW1NvlOnxzVBQXK3HD
rUck4dxa0t30wUFK0XVQjNEArXqvU23EB8Z7bQQMRx0yhd4pF5k29Q==
-----END RSA PRIVATE KEY-----
"""

### for a PI
public_key3="""ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA9LrXvUvGZK092R+0+xNZAOUrywDmfdtOL2XqtO26PCjns2GmxLmphJkvBBtXCt4d8s9jdPILHKnTC0/8/WfrwhZ68AWHay1qnCnWjgMUFEg2J4+MsT0UpirQ7wQbA3KeuAVobRaMIdfgPwlgnmBu2VyPiS4eD4KDz2CgL2DIWzq+DzrakOSqS6eb5MMNS7rIDlxH0WV9bTueweoeWi77zpEtA4sA4EFRKZ21uNyceQ/ob8mKC1yAz2XGIKoLgaxRvd+d8Mmq52OLzbCPtDCnCAtWW2PJt8hEjR+RKwYhf0NcpMXhA5GsYAXUFmHUI0j0f/8qodWuIorE/5zr4EVVkQ== pi@test.onelab.eu
"""

private_key3="""
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEA9LrXvUvGZK092R+0+xNZAOUrywDmfdtOL2XqtO26PCjns2Gm
xLmphJkvBBtXCt4d8s9jdPILHKnTC0/8/WfrwhZ68AWHay1qnCnWjgMUFEg2J4+M
sT0UpirQ7wQbA3KeuAVobRaMIdfgPwlgnmBu2VyPiS4eD4KDz2CgL2DIWzq+Dzra
kOSqS6eb5MMNS7rIDlxH0WV9bTueweoeWi77zpEtA4sA4EFRKZ21uNyceQ/ob8mK
C1yAz2XGIKoLgaxRvd+d8Mmq52OLzbCPtDCnCAtWW2PJt8hEjR+RKwYhf0NcpMXh
A5GsYAXUFmHUI0j0f/8qodWuIorE/5zr4EVVkQIBIwKCAQAN/AxT9bOQuXE/m2lt
btHiy0RUvjkOgY9wbDlMKtdxJuirKibJabHqUeVt8u8H729s9ehtFSU01oEWlttB
riq6ojLpJOMqsiNZYXn5fITN9X9v+ZMC0EpSo1xlbfLqQRBiSXOudlEmgV1FbkAJ
DNMiXQ+ELoVf+NRU/jUKBYfKssmuwptMuBUvAksTF/bq1P6vaYP2GluEAKSvZjhb
jc78LMxd1G+rmVX7wmV1dzgscB+d5kvb4lO7gZdJQlGwDxIvGKfAU9oNoIHXt+x4
TJrNq5+w3DD7VXZx/O2K382HJKmgxZsfHatBZDiEDPnwHYM5BEGa6EJpuKilpHUa
CSkLAoGBAPvjOw6vSTdJPS11KRV3H+2PDxfqRRiHheZ1fXeL7SUQHaSLwJhCgB9Q
gTGy6xbGvDLz557ninkh6I4EOaZBZBI3DIFxG/ZZcmEdMIrf4kpFF4yXW/ujjdHk
uqUX09FBRBPodvZRuHNLXg6g/0uWd7sIuUx/GMQjo37v6W54TuXpAoGBAPi5si4j
BgBLwkyhdpbHC3GBlqqUUyNfqnZO78yMEDCBY5ANxMZixdEjUpR+Sy6oqYwwo7ub
2U5cIWCaZ8+3QIFOo6TZ8kyfeEpxbVqbEcezuF8s+nTl4tndmq8U5cOA/bA+zNAR
UgQcTehuf3KizMERe2IL3F/Ex7689XwgViFpAoGAelhtJGPEefBfixumPaBCtTbb
cgQS7qg5uRR+xQlzL0JXim/D8i7txhEozv8hupsK9C1TPo24SXbeq2EjUMCs8ueJ
uzbwUxWAstOp3Q2obTeAd3y3phw9kdV/Oj7F9+yAJu1BGI4Xwvi4qAUOSUkVlVwC
OxkpSVMjhsxMz0G/7AMCgYAcbP5rrDszO9uw/IKU44xHfIY/YWiWVBN7PDipqZtz
QfzAAZLU2BabjwIfmWetj55ZKiFXRQLkYkz1GPXr2m3FopZb+6apq9M7tTERq1J9
ORxipg3+uy/eYngUAmNmzOnK/9zklEPjNm9Nw3xHnZO+SyQLNI421KkdHOja/GGd
awKBgQCLtk0+RpswH451PWyAJ6F+U4YDVaHR0s6pwp4TJAkDVlFBiRO28jEb5y0N
bI1R7vrRdq07SgI3USLXqDokQ/pXJhC03w2r7W7niAkNaUll3YtJ2DZVSvuQguR9
xwRNsuo0x60e7bivU+kNZtLn5FqWuGoBONZnbhgP6y7jPsNrig==
-----END RSA PRIVATE KEY-----
"""

def keys (options,index):
    return [ {'name': 'key1',
              'private' : private_key,
              'key_fields' : {'key_type':'ssh',
                              'key': public_key}},
             {'name': 'key2',
              'private' : private_key2,
              'key_fields' : {'key_type':'ssh',
                              'key': public_key2}}
             ]

############################## initscripts
initscript_by_name="""#!/bin/bash
command=$1; shift
slicename=$1; shift
stamp="the_script_name"
stampfile=/tmp/$stamp.stamp

echo "Running initscript with command=$command and slicename=$slicename"

function start () {
  (echo Starting test initscript: $stamp on slicename $slicename ; date) >> $stampfile
  echo "This is the stdout of the sliver $slicename initscript $command (exp. start) pid=$$" 
  echo "This is the stderr of the sliver $slicename initscript $command (exp. start) pid=$$" 1>&2
}
function stop () {
  echo "Removing stamp $stampfile"
  rm -f $stampfile
}
function restart () {
  stop
  start
}
case $command in 
start) start ;;
stop) stop ;;
restart) restart ;;
*) echo "Unknown command in initscript $command" ;;
esac
"""

initscript_by_code=initscript_by_name.replace("the_script_name","the_script_code")

# one single initscript in the InitScripts table
def initscripts(options,index): 
    return [ { 'initscript_fields' : { 'enabled' : True,
                                       'name':'the_script_name',
                                       'script' : initscript_by_name,
                                       }},
             ]

# always return 2 slices
# one has an initscript code, the other one an initscript name
def slices (options,index):
    def theslice (i):
        slice_spec = { 'slice_fields': {'name':'%s_sl%d'%(login_base(index),i),
                                        'instantiation':'plc-instantiated',
                                        'url':'http://foo%d.com'%index,
                                        'description':'testslice number %d'%i,
                                        'max_nodes':2,
                                        },
                       'usernames' : [ 'pi','user','techuser' ],
                       'nodenames' : all_nodenames(options,index),
                       'sitename' : login_base(index),
                       'owner' : 'pi',
                       }
        # odd one has an initscript_code
        if i%2==1:
            slice_spec['initscriptcode']=initscript_by_code
            slice_spec['initscriptstamp']='the_script_code'
        # even one has an initscript (name)
        else:
            slice_spec['initscriptname']='the_script_name'
            slice_spec['initscriptstamp']='the_script_name'
        return slice_spec
    return [ theslice(i) for i in range (2*index-1,2*index+1) ]

def all_slicenames (options,index):
    return [ slice['slice_fields']['name'] for slice in slices(options,index)]

def tcp_tests (options,index):
    if index == 1:
        return [
            # local test
            { 'server_node': 'node1',
              'server_slice' : '%s_sl1'%login_base(index),
              'client_node' : 'node1',
              'client_slice' : '%s_sl1'%login_base(index),
              'port' : 2000,
              }]
    elif index == 2:
        return [
            # remote test
            { 'server_node': 'node2',
              'server_slice' : '%s_sl3'%login_base(index),
              'client_node' : 'node2',
              'client_slice' : '%s_sl4'%login_base(index),
              'port' : 4000,
              },
            ]
    else:
        return []

# the semantic for 't_from' and 't_until' here is:
# if they are smaller than one year, they are relative to the current time, expressed in grains
# otherwise they are absolute
def leases (options, index):
    leases=[]
    counter=0
    slices=all_slicenames(options,index)
    slice_sequence = slices[:1] + slices + [None,]
    for iterator in range(12):
        for slice in slice_sequence:
            leases.append ( {'slice' : slice, 't_from':counter,'t_until':counter+1} )
            counter += 1
    return leases

def plc (options,index) :
    return { 
        'index' : index,
        'name' : 'plctest%d'%index,
        # as of yet, not sure we can handle foreign hosts, but this is required though
        'host_box' : 'deferred-myplc-hostbox-%d'%index,
        # set these two items to run within a vserver
        'vservername': 'deferred-vservername',
        'vserverip': 'deferred-vserverip',
        'role' : 'root',
        'PLC_NAME' : 'Regression TestLab',
        'PLC_ROOT_USER' : 'root@test.onelab.eu',
        'PLC_ROOT_PASSWORD' : 'test++',
        'PLC_SLICE_PREFIX' : 'auto',
        'PLC_SHORTNAME' : 'Rlab',
        'PLC_MAIL_ENABLED':'false',
        'PLC_MAIL_SUPPORT_ADDRESS' : 'thierry.parmentelat@inria.fr',
        'PLC_DB_HOST' : 'deferred-myplc-hostname',
#        'PLC_DB_PASSWORD' : 'mnbvcxzlkjhgfdsapoiuytrewq',
        'PLC_API_HOST' : 'deferred-myplc-hostname',
        'PLC_WWW_HOST' : 'deferred-myplc-hostname',
        'PLC_BOOT_HOST' : 'deferred-myplc-hostname',
        'PLC_NET_DNS1' : 'deferred-dns-1',
        'PLC_NET_DNS2' : 'deferred-dns-2',
        'PLC_RESERVATION_GRANULARITY':1800,
        # minimal config so the omf plugins actually trigger
        'PLC_OMF_ENABLED' : 'true',
        'PLC_OMF_XMPP_SERVER': 'deferred-myplc-hostname',
        'sites' : sites(options,index),
        'keys' : keys(options,index),
        'initscripts': initscripts(options,index),
        'slices' : slices(options,index),
        'tcp_test' : tcp_tests(options,index),
	'sfa' : sfa(options,index),
        'leases' : leases (options, index),
    }

# NOTE: SFA currently has SFA_AGGREGATE_API_VERSION=2 baked into the code
def sfa (options,index) :
    return { 
        # the default is to use AMs in the various aggregates.xml
        # stack config_sfamesh to point to SMs instead
        'neighbours-port':12346,
        ## global sfa-config-tty stuff
        'SFA_REGISTRY_ROOT_AUTH' : sfa_root(index),
        'SFA_INTERFACE_HRN' : sfa_root(index),
	'SFA_REGISTRY_HOST' : 'deferred-myplc-hostname',
	'SFA_AGGREGATE_HOST': 'deferred-myplc-hostname',
	'SFA_SM_HOST': 'deferred-myplc-hostname',
	'SFA_PLC_URL' : 'deferred-myplc-api-url',
        'SFA_PLC_USER' : 'root@test.onelab.eu',
        'SFA_PLC_PASSWORD' : 'test++',
# use -c sfadebug to increment this one
        'SFA_API_LOGLEVEL': 1,
# use -c sfavoid to set this to 'void'
        'SFA_GENERIC_FLAVOUR' : 'pl',
        'SFA_AGGREGATE_ENABLED' : 'true',
        # details of the slices to create
        'sfa_slice_specs' : [ sfa_slice_spec(options,index,rspec_style) 
                              for rspec_style in options.rspec_styles ]
    }

# rspecstyle is 'pl' for sfav1 or 'pg' for pgv2
def sfa_slice_spec (options,index,rspec_style):
    the_login_base=sfa_login_base(index,rspec_style)
    # we're already in a dedicated site/authority so no need to encumber with odd names
    piuser='pi'
    pimail=piuser+'@test.onelab.eu'
    regularuser='us'
    slicename='sl'
    prefix='%s.%s'%(sfa_root(index),the_login_base)
    hrn=prefix+'.'+slicename
    user_hrn=prefix+'.'+regularuser
    pi_hrn=prefix+'.'+piuser
    key=public_key2
    mail="%s@%s"%(regularuser,domain)
    person_record_xml =\
'''<record hrn="%(user_hrn)s" type="user" email="%(mail)s" enabled="True" 
first_name="Fake" last_name="Sfa style=%(rspec_style)s" >
<keys>%(key)s</keys>
<roles>user</roles>
<roles>tech</roles>
</record>'''%locals()
    slice_record_xml =\
'''<record hrn="%s" type="slice" description="SFA-testing" url="http://test.onelab.eu/">
<researcher>%s</researcher>
</record>'''%(hrn, user_hrn)


    return { 'slice_fields': {'name':'%s_%s'%(the_login_base,slicename),
                              'url':'http://foo%d@foo.com'%index,
                              'description':'SFA-testing',
                              'max_nodes':2,
                              },
             'login_base' : the_login_base,
             'piuser' : piuser,
             'pimail' : pimail,
             'regularuser':regularuser,
             'domain':domain,
             'usernames' : [ (regularuser,'key2') ],
             'nodenames' : all_nodenames(options,index),
             'sitename' : the_login_base,
             'slicename' : slicename,
             'slice_record' : slice_record_xml,
             'person_record' : person_record_xml,
             'rspec_style':rspec_style,
             } 


def config (plc_specs,options):
    result=plc_specs
    for i in range (options.size):
        result.append(plc(options,i+1))
    return result
