# -*- python3 -*-
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2015 INRIA 
#
# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# values like 'hostname', 'ip' and the like are rewritten later with a TestPool object

pldomain = "onelab.eu"

### for the sfa dual setup
def login_base (index): 
    if index == 1: return 'inri'
    elif index == 2: return 'princ'
    # index=3=>'sitea'  4=>'siteb' 
    else: return 'site{}'.format(chr(index+94))

# only one rspec style
def sfa_login_base (index):
    return "sfa"

def sfa_root (index):
    # use plt (planetlab test) instead of pl
    # otherwise a triangular test ends up with 'plc'
    # plta, pltb, ...
    return '{}'.format(chr(index+96))

def nodes(options, index):
    return [{'name' : 'node{}'.format(index),
             'node_fields':  { 'hostname' : 'deferred-nodename{}'.format(index),
                               'model' : 'qemu/minhw', } ,
             'host_box' : 'deferred-node-hostbox-{}'.format(index),
             'owner' : 'pi',
             'nodegroups' : 'mynodegroup',
             'interface_fields':        { 'method' : 'static',
                                          'type' : 'ipv4',
                                          'ip' : 'xxx-deferred-xxx',
                                          'gateway' : 'xxx-deferred-xxx',
                                          'network' : 'xxx-deferred-xxx',
                                          'broadcast' : 'xxx-deferred-xxx',
                                          'netmask' : 'xxx-deferred-xxx',
                                          'dns1' : 'xxx-deferred-xxx',
                                          'dns2' : 'xxx-deferred-xxx',
                                          },
             ######## how to deal with the new plcapi way of modeling interfaces
             # this pertains to the node as per the new interface - using UpdateNode
             # after node_fields above is used to create the Node
             'node_fields_nint' :       { 'dns' : 'xxx-deferred-xxx',
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
             'bootmedium_options' :     [ 'serial', 'no-hangcheck', 'systemd-debug' ],
             'tags'               :     {
                 # no tags anymore
             },
             # boot cd settings
             # we should have tags here instead of the hard-wired
             # options set for GetBootMedium in TestNode.py
             }]

def all_nodenames (options, index):
    return [ node['name'] for node in nodes(options, index)]

def users (options) :
    return [ 
        {'name' : 'admin', 'key_names' : [ 'key_admin' ],
         'user_fields' : {'first_name' : 'Admin',
                          'last_name' : 'Admin',
                          'enabled' : 'true',
                          'email' : 'admin@{}'.format(pldomain),
                          'password' : 'testuseradmin'},
         'roles':['admin']},

        {'name' : 'pi', 'key_names' : [ 'key_pi' ],
         'user_fields' : {'first_name' : 'PI', 'last_name' : 'PI',
                          'enabled' : 'True',
                          'email' : 'fake-pi1@{}'.format(pldomain),
                          'password' : 'testpi'},
         'roles':['pi']},

        {'name' : 'pitech', 'key_names' : [ 'key_pi' ],
         'user_fields' : {'first_name' : 'PiTech',
                          'last_name' : 'PiTech',
                          'enabled' : 'true',
                          'email' : 'fake-pi2@{}'.format(pldomain),
                          'password' : 'testusertech'},
         'roles':['pi','tech']},

        {'name' : 'tech', 'key_names' : [ 'key_user' ],
         'user_fields' : {'first_name' : 'Tech', 'last_name' : 'Tech',
                          'enabled' : 'true',
                          'email' : 'fake-tech1@{}'.format(pldomain),
                          'password' : 'testtech'},
         'roles':['tech']},

        {'name' : 'user', 'key_names' : [ 'key_user' ],
         'user_fields' : {'first_name' : 'User', 'last_name' : 'User',
                          'enabled' : 'true',
                          'email' : 'fake-user1@{}'.format(pldomain),
                          'password' : 'testuser'},
         'roles':['user']},

        {'name' : 'techuser', 'key_names' : [ 'key_user' ],
         'user_fields' : {'first_name' : 'UserTech', 'last_name' : 'UserTech',
                          'enabled' : 'true',
                          'email' : 'fake-tech2@{}'.format(pldomain),
                          'password' : 'testusertech'},
         'roles':['tech','user']},

        ]

def all_usernames (options):
    return [ user['name'] for user in users(options)]

def sites (options, index):
    latitude  = -90 + (index*10)
    longitude = -180 + (index*20)
    return [ {'site_fields' : {'name' : 'main site for plc number {}'.format(index),
                               'login_base':login_base(index),
                               'abbreviated_name' : 'PlanetTest{}'.format(index),
                               'max_slices':100,
                               'url' : 'http://test.{}'.format(pldomain),
                               'latitude':float(latitude),
                               'longitude':float(longitude),
                               },
              'address_fields' : {'line1' : 'route des lucioles',
                                  'city' : 'sophia',
                                  'state' : 'fr',
                                  'postalcode' : '06600',
                                  'country' : 'France',
                                  },
              'users' : users(options),
              'nodes': nodes(options, index),
            }]

##########
# key0 -> planetlab admin
# key1 -> planetlab PI
# key2 -> planetlab user
# key3 -> sfa PI
# key4 -> sfa user
public_key0 = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3okOugCBs2j/uur/lBdNUqWG0VdLdrELy85MR6mGOER5ijdbZekEG6KD4zzG2fwXOzdGF99HTQAOXvty02V5/sBN/GbT1Rehwh3cUvZ8i3aJIdN4ku+zbWK6CBsQ8XGXMpCImALDxcvcaoToWJbephDpkgKtcBwmowmOQswO4GTzIdT217J13Z860Jz/QJPIjloS7HpuLmKVlZ/sWCYcuKmR4X7evCXrvbHh+iamSrOHV9sQ6Sf0Wu+VJRaUN92BrxVi9zuJNWZWtWWWjLecyaooOVS0UMBZKUNbnuGXSJ8IFHfQ9wpGGsG+KohvGH4Axh3utaDOlUG641iM5GVBX planetlab-admin@test.onelab.eu
"""

private_key0 = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAt6JDroAgbNo/7rq/5QXTVKlhtFXS3axC8vOTEephjhEeYo3W
2XpBBuig+M8xtn8Fzs3RhffR00ADl77ctNlef7ATfxm09UXocId3FL2fIt2iSHTe
JLvs21iuggbEPFxlzKQiJgCw8XL3GqE6FiW3qYQ6ZICrXAcJqMJjkLMDuBk8yHU9
teydd2fOtCc/0CTyI5aEux6bi5ilZWf7FgmHLipkeF+3rwl672x4fompkqzh1fbE
Okn9FrvlSUWlDfdga8VYvc7iTVmVrVlloy3nMmqKDlUtFDAWSlDW57hl0ifCBR30
PcKRhrBviqIbxh+AMYd7rWgzpVBuuNYjORlQVwIDAQABAoIBAQCSvuT/SfyfgDme
+TXoOyOKgGFHz13XL5XAuM1Kf9a9xQhXEaoj2QKmFrisnEbJ4/AsN2W8fTH8cydr
2GZfT2Wo/HhYFZ76cocxhc+vj2jgX+UTqfDrwhGhp9isp+OhqOThCDkRzXOZP5og
eb8Fe9atbLGNJxXJUQZzCgSu2Z+bOZMhh983DNB7porEhcB21Ja86a6VzIW0ieM0
WxeVuQfPPGH1U6wGr3rVwKF0tXQHlMg48KNmpvahwS89Ihp1VIBzSNlVXkZ9O5Fc
wmBQGNoeM32/N+8yHVYkdTHIrvi5mm52KMwhDGg0lXDjrXAIe+rCzuigv5kIsmuA
fqu6Co8hAoGBAPJF7xDGVYjOObQ/ckdpQ76ntJcNMIVa4XoL0cn9NFBhvV1ooRTn
KASHH9Wj+sWYkZDm4wmWgaIthnQb2F1Rq/8FmJaPlCVQZtLDydDI7spLF+ixVxCk
y8nhCr+cad9yPJ8ozYP2vMs9gBheDaL8LBDUdPyuC94e2TQy0fqW0rJFAoGBAMIJ
yvATDuF4Zssn4gOpRkyP9fjdrnIo5YKF9aCjv/j984XexwRqAwvSMqykmUnwF4Yg
rWjV+1Jw9lJuAIMUdiIH3fqPGBeOrpvES5Kmi1FFB5ufA1Hcpe9LNJSiuNMYemCB
rDnfoG2cW1lCwrb5y8ROOUp2OAQ5jJQyPjV08S/rAoGARZ0An1JN23xeKkOcw5Yk
iBDKHCkHCxpc9WOWCTL/KCWdcsyQlGADKKHm7M0sTkCTew5MqEGdyArKumwR1GaW
RDXIbWKeD8a1dNQbFinWKzw+h3cFbFvdzokiPIJmDXVWo+jmfIeWIdPvDZFg27cX
tlJFtyEPeehlQtFjclyJ9/0CgYEAuDht6MJfVWdnSKfj6A/1Q0lGgXGOZqo3RFWE
n2/4GiCY7NdWYfV4UOfO3qQjONRusRQjLy5BPsMqyZXQfKKXibWoZXMnr23yjsat
7VybVpxQHcq5byYqkGb5U8it6xUJUsiqSAPtn0NcYwGENg4xDH4r3GsiwbgVpLmS
4FPXjOMCgYA40bzt7QjKBURj3A9nMrFpbg1dQjNZv7ThnDq2KcLlQxusddSO3Tou
capLbON5tuaHbiGGVYSiUCHC6HXYWN7JGytpAjAYZhLWmK7ltNMlDQA9FX8LktPE
UToHxiKAuREDgRP9waHmk16833hNe8tDvX5P9vKWxx1AtZRuJoFozw==
-----END RSA PRIVATE KEY-----
"""

public_key1 = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4jNj8yT9ieEc6nSJz/ESu4fui9WrJ2y/MCfqIZ5WcdVKhBFUYyIenmUaeTduMcSqvoYRQ4QnFR1BFdLG8XR9D6FWZ5zTKUgpkew22EVNeqai4IXeWYKyt1Qf3ehaz9E3o1PG/bmQNIM6aQay6TD1Y4lqXI+eTVXVQev4K2fixySjFQpp9RB4UHbeA8c28yoa/cgAYHqCqlvm9uvpGMjgm/Qa4M+ZeO7NdjowfaF/wF4BQIzVFN9YRhvQ/d8WDz84B5Pr0J7pWpaX7EyC4bvdskxl6kmdNIwIRcIe4OcuIiX5Z9oO+7h/chsEVJWF4vqNIYlL9Zvyhnr0hLLhhuk2bw== planetlab-pi@test.onelab.eu
"""
private_key1 = """-----BEGIN RSA PRIVATE KEY-----
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
public_key2 = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQLvh5LkrjyLIr9UJznTJHMnqjdqzRdc9ekVmI9bx/5X4flnGtPBsr6bK/CPXmWjS2Vw0QOxi1NM45qkQJZXxroS0aehCCrvJRHgp/LOZykWCyNKqVopq9w0kH4jw1KFGIuwWROpOcMq2d/kAwyr6RV/W66KNVqu2XDiNOPJLcuZCuKrH++q3fPyP2zHSJ/irew7vwqIXbDSnVvvyRXYgc9KlR57L4BWthXcUofHlje8wKq7nWBQIUslYtJDryJg5tBvJIFfCFGmWZy0WJlGJd+yppI5jRvt9c6n9HyJKN22lUBTaTaDFvo+Xu5GEazLKG/v8h/o5WpxrrE6Y3TKeX planetlab-user@test.onelab.eu
"""

private_key2 = """
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
public_key3 = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA9LrXvUvGZK092R+0+xNZAOUrywDmfdtOL2XqtO26PCjns2GmxLmphJkvBBtXCt4d8s9jdPILHKnTC0/8/WfrwhZ68AWHay1qnCnWjgMUFEg2J4+MsT0UpirQ7wQbA3KeuAVobRaMIdfgPwlgnmBu2VyPiS4eD4KDz2CgL2DIWzq+DzrakOSqS6eb5MMNS7rIDlxH0WV9bTueweoeWi77zpEtA4sA4EFRKZ21uNyceQ/ob8mKC1yAz2XGIKoLgaxRvd+d8Mmq52OLzbCPtDCnCAtWW2PJt8hEjR+RKwYhf0NcpMXhA5GsYAXUFmHUI0j0f/8qodWuIorE/5zr4EVVkQ== sfa-pi@test.onelab.eu
"""

private_key3 = """
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
xwRNsuo0x60e7bivU+kNZtLn5FqWuGoBONZnbhgP6y7jPsNrig == 
-----END RSA PRIVATE KEY-----
"""

public_key4 = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDIim+K+tfwI7KcfbtX/FB1DQCWU1RY8eH4b18KywxI3DDuHa4jGvPjeU5WPwfOsUFpWcWMXCmA26TSOmeT2HiiSJNLUKB0keu/PtHAGnn6rFv5YjCF2fa65wZVkEy6eb8buBny+2L5jhFPW0KE4JNTCiueAEbWZInTWmdA1WB8QeTV3USi33NTtYE05I2/x4G2BtFmmzWzCuyRVjkWZQPJY6wIyM1+qGixpbacScxYYDBGA0I9N9VSN9OS2BN3GY8xFJjFSD2+GxsUhDUmUw2bO8ppn2OSl8NUW/U4EQzUTP8VhebI6UqjfIGAv5qHPpe0Yrcrd/QlbWvj2zpqvVtX sfa-user@test.onelab.eu
"""

private_key4 = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAyIpvivrX8COynH27V/xQdQ0AllNUWPHh+G9fCssMSNww7h2u
Ixrz43lOVj8HzrFBaVnFjFwpgNuk0jpnk9h4okiTS1CgdJHrvz7RwBp5+qxb+WIw
hdn2uucGVZBMunm/G7gZ8vti+Y4RT1tChOCTUworngBG1mSJ01pnQNVgfEHk1d1E
ot9zU7WBNOSNv8eBtgbRZps1swrskVY5FmUDyWOsCMjNfqhosaW2nEnMWGAwRgNC
PTfVUjfTktgTdxmPMRSYxUg9vhsbFIQ1JlMNmzvKaZ9jkpfDVFv1OBEM1Ez/FYXm
yOlKo3yBgL+ahz6XtGK3K3f0JW1r49s6ar1bVwIDAQABAoIBAQCQbJKURr8JJMxX
Q32OihnvkmOf33dZbynMX3jVLxIzztA2TI3CnoCSjCRMnKwkwSdYldxdj2occRKs
jH9XzIhkZ1wc234TNZvQaY9piCfczhCW8436d9TnGcZIDNoVWeS2M8oMYdsP2q7A
tfqb85hmL2bmLVDWyiUwX2UJHiKUmSGzUUKqI0RCnvt2XioSVSvvo+DWz+aA/GR+
rvl7EyniqA93gvP7kduOJ95CGUbgJuO3Kay5zq1YaR0LawxsiEHaK75/unFpbVmd
FqB1h7srfHJWhrRW9NQs1YFFeDIGZ+dDuFKwPSxe9EmT4q/4Uu2LnnR4AkluPzog
9KhUa1MxAoGBAOSqSSiD1fwbvqHu3z/gl7YouSCB78RnnvTdRhzMeqpWNuy/c20l
nkD8NZBTBSXQGoU4hY83ncsA+PBc0HbI3ZJyEBySdp7b5rE79+xRnXpsV5PARnkb
FbaMeu8RuM1rVUQYRpp8hawo5iycV5IFeQZ3jhB1gunTR3kVgNxSIcdlAoGBAOCD
eVkfUcPQ/TqE1QoXYg1UTz1ZLB0Iton7UJ9G7cLkg53dyPPrh+MgzZSWh5DnmBSd
Dj+XjYbCPvShQsnMoyjlFcXpuG+6ebyig2F8w6FKKkrB5r9pzP3237jBZZquX4De
PwOHC2lNOoBIbv+VnlpSjx2XMDrGkIQwWUwonwILAoGBAJmQ1vLznwjh5SPBVYMD
pT97l+CCAvEnGfSeihCbLqIoplhWtwENK3u/JYXYi3N6j+T6MZAeLMWB0K0z1/h+
K3fHTJSztCA51HMgr/6wTQ9DpYkfrvR0QR/ItmLJxw+FzsyddQUZLXiSOwqosJLr
Q/0Y23qoQJQiBTUHQPQ14GOVAoGBAL2T5uStgJJzp1BBl860nfQZa+umn4xIrjJn
BtXnw56c7NJh02y8RnswWMeOMBzYol9NmxlxdG0FGrngbZAO/vrqLe93gmi9skvp
gjzQaDSKdpm3j4uz4AfW7WSJ0azCbxxXDiiBYM5jCvIFt8yTXypvqi9XWb9XqfIl
DVI0vsevAoGAb0SgdcyRcIrozl7Rky1GUTcCPXGMCCts9kMWNucWq6jvkCo8YdH1
b+fHzZFpKJNbpROjJ1er3U5jg6qtA32mbuQ9IhoYqtLISJqV+MO36pDFmjPng0+D
NhwboXV6u+hSpUHGK+MmqGgKkkZI6KRwTT+NWZY2FTX3UOl8IMymTBk=
-----END RSA PRIVATE KEY-----
"""

master_key_index = {
    'key_admin':    {'private':private_key0, 'public':public_key0},
    'key_pi':       {'private':private_key1, 'public':public_key1},
    'key_user':     {'private':private_key2, 'public':public_key2},
    'key_sfapi':    {'private':private_key3, 'public':public_key3},
    'key_sfauser':  {'private':private_key4, 'public':public_key4},
}

plc_key_names = [ 'key_admin', 'key_pi', 'key_tech' ]

# expose a list of key_specs
#  { 'key_name':<>, 'private':<>, 'public':<>, 'in_plc':<bool>, key_fields: <for AddKey>, }
def keys (options, index):
    result = []
    for (key_name, priv_pub) in master_key_index.items():
        private = priv_pub['private']
        public = priv_pub['public']
        result.append( { 'key_name': key_name,
                         'private':private,
                         'public':public,
                         'in_plc': key_name in plc_key_names,
                         'key_fields' : {'key_type' : 'ssh',
                                         'key': public},
                         } )
    return result

############################## initscripts
initscript_by_name = """#!/bin/bash
command=$1; shift
slicename=$1; shift
stamp="initscript_by_name"
stampfile=/var/tmp/$stamp.stamp
date=$(date)

echo $date "Running initscript with command=$command and slicename=$slicename"

function start () {
  (echo $date Starting test initscript: $stamp on slicename $slicename ; date) >> $stampfile
  echo $date "This is the stdout of the sliver $slicename initscript $command (exp. start) pid=$$"
  echo $date "This is the stderr of the sliver $slicename initscript $command (exp. start) pid=$$" 1>&2
}
function stop () {
  echo $date "Removing stamp $stampfile"
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

initscript_by_code = initscript_by_name.replace("initscript_by_name","initscript_by_code")

# one single initscript in the InitScripts table
def initscripts(options, index): 
    return [ { 'initscript_fields' : { 'enabled' : True,
                                       'name' : 'initscript_by_name',
                                       'script' : initscript_by_name,
                                       }},
             ]

# returns 3 slices
# 1 has an initscript code
# 2 has an initscript name
# 3 used to be an omf-friendly slice but this is now deprecated
def slices (options, index):
    def theslice (i):
        slice_spec = { 'slice_fields': {'name' : '{}_sl{}'.format(login_base(index),i),
                                        'instantiation' : 'plc-instantiated',
                                        'url' : 'http://foo{}.com'.format(index),
                                        'description' : 'testslice number {}'.format(i),
                                        'max_nodes':2,
                                        },
                       'usernames' : [ 'pi','user','techuser' ],
                       'nodenames' : all_nodenames(options, index),
                       'sitename' : login_base(index),
                       'owner' : 'pi',
                       }
        # 1st one has an initscript by code
        if i%3 == 1:
            slice_spec['initscriptcode'] = initscript_by_code
            slice_spec['initscriptstamp'] = 'initscript_by_code'
        # 2nd one has an initscript by name
        elif i%3 == 2:
            slice_spec['initscriptname'] = 'initscript_by_name'
            slice_spec['initscriptstamp'] = 'initscript_by_name'
        # 3rd one - not omf-friendly any longer
        else:
            # omf-friendly slices is a deprecated feature
            # slice_spec ['omf-friendly'] = True
            pass
        return slice_spec
    # usual index is 1, additional plc's then get 2...
    # so index=1 -> 1 - 2 - 3
    #    index=2 -> 4 - 5 - 6
    # 3 * (index-1) + 1 = 3*index-2  .. same+3 = 3*index+1
    return [ theslice(i) for i in range (3*index-2,3*index+1) ]

def all_slicenames (options, index):
    return [ slice['slice_fields']['name'] for slice in slices(options, index)]

# the logic here is to try:
# . client and server on the same slice/node
# . client and server on the same node but 2 different slices
# if at least 2 plcs, we have 2 nodes, so again on diff. nodes
def tcp_specs (options, index):
    # only run the test on the first plc
    if index != 1: return None
    # 
    slice1 = '{}_sl1'.format(login_base(1))
    slice2 = '{}_sl2'.format(login_base(1))
    # with the addition of omf-friendly slices..
    slice3 = '{}_sl4'.format(login_base(2))
    slice4 = '{}_sl5'.format(login_base(2))

# NOTE: port 9999 is hard-wired in the code to be used for checking network readiness
# so it is not to be used here
# bind on 0.0.0.0 and try to reach this on localhost
# not expected to work
    same_node_same_slice_lo =   { 'server_node' : 'node1', 'server_slice': slice1,
                                  'client_node' : 'node1', 'client_slice': slice1,
                                  'client_connect' : 'localhost',
                                  'port': 10000}
    same_node_same_slice =      { 'server_node' : 'node1', 'server_slice': slice1,
                                  'client_node' : 'node1', 'client_slice': slice1,
                                  'port': 10001}
# this does not work on vs-nodes....
    same_node_2_slices =        { 'server_node' : 'node1', 'server_slice': slice1,
                                  'client_node' : 'node1', 'client_slice': slice2,
                                  'port': 10002}
    two_nodes_same_slice =      { 'server_node' : 'node1', 'server_slice': slice1,
                                  'client_node' : 'node2', 'client_slice': slice3,
                                  'port': 10003}
    two_nodes_2_slices =        { 'server_node' : 'node1', 'server_slice': slice1,
                                  'client_node' : 'node2', 'client_slice': slice4,
                                  'port': 10004}
    specs = []
#    specs += [ same_node_same_slice_lo ]
    specs += [ same_node_same_slice ]
# worth another try
    specs += [ same_node_2_slices ]
    if options.size > 1:
        specs += [ two_nodes_same_slice, two_nodes_2_slices ]
    return specs

# the semantic for 't_from' and 't_until' here is:
# if they are smaller than one year, they are relative to the current time, expressed in grains
# otherwise they are absolute
def leases (options, index):
    leases = []
    counter = 0
    slices = all_slicenames(options, index)
    slice_sequence = slices[:1] + slices + [None,]
    for iterator in range(12):
        for slice in slice_sequence:
            leases.append ( {'slice' : slice, 't_from' : counter, 't_until' : counter + 1 } )
            counter += 1
    return leases

def plc (options, index) :
    return { 
        'index' : index,
        'name' : 'plctest{}'.format(index),
        # as of yet, not sure we can handle foreign hosts, but this is required though
        'host_box' : 'deferred-myplc-hostbox-{}'.format(index),
        # set these two items to run within a vserver
        'vservername' : 'deferred-vservername',
        'vserverip' : 'deferred-vserverip',
        'role' : 'root',
        # these go to plc-config-tty
        'settings': {
            'PLC_NAME' : 'Regression TestLab',
            'PLC_ROOT_USER' : 'root@test.onelab.eu',
            'PLC_ROOT_PASSWORD' : 'test++',
            'PLC_SLICE_PREFIX' : 'auto',
            'PLC_HRN_ROOT': sfa_root(index),
            'PLC_SHORTNAME' : 'Rlab',
            'PLC_MAIL_ENABLED' : 'false',
            'PLC_MAIL_SUPPORT_ADDRESS' : 'thierry.parmentelat@inria.fr',
            'PLC_DB_HOST' : 'deferred-myplc-hostname',
#            'PLC_DB_PASSWORD' : 'mnbvcxzlkjhgfdsapoiuytrewq',
            'PLC_API_HOST' : 'deferred-myplc-hostname',
            'PLC_WWW_HOST' : 'deferred-myplc-hostname',
            'PLC_BOOT_HOST' : 'deferred-myplc-hostname',
            'PLC_NET_DNS1' : 'deferred-dns-1',
            'PLC_NET_DNS2' : 'deferred-dns-2',
            'PLC_RESERVATION_GRANULARITY':1800,
            'PLC_VSYS_DEFAULTS' : ' , vif_up, vif_down, fd_tuntap, promisc, ',
# omf-friendly slices is a deprecated feature
#            'PLC_OMF_ENABLED' : 'true',
#            'PLC_OMF_XMPP_SERVER' : 'deferred-myplc-hostname',
            'PLC_OMF_ENABLED' : 'false',
        },
        'expected_vsys_tags': [ 'vif_up', 'vif_down', 'fd_tuntap', 'promisc', ],
        # minimal config so the omf plugins actually trigger
        'sites' : sites(options, index),
        'keys' : keys(options, index),
        'initscripts': initscripts(options, index),
        'slices' : slices(options, index),
        'tcp_specs' : tcp_specs(options, index),
        'sfa' : sfa(options, index),
        'leases' : leases (options, index),
        # big distros need more time to install nodes
        'ssh_node_boot_timers': (40,38),
        'ssh_node_debug_timers': (10,8),
    }

def sfa (options, index) :
    return { 
        # the port used to generate the various aggregates.xml
        # stack config_sfamesh to point to SMs instead
        'neighbours-port':12346,
        # the port that sfi connects to - used to be 12347 when the SM was still running
        # but now the SM is just turned off for these tests
        'sfi-connects-to-port' : 12346,
        ## global sfa-config-tty stuff
        'settings': {
            'SFA_REGISTRY_ROOT_AUTH' : sfa_root(index),
            'SFA_INTERFACE_HRN' : sfa_root(index),
            'SFA_REGISTRY_HOST' : 'deferred-myplc-hostname',
            'SFA_AGGREGATE_HOST' : 'deferred-myplc-hostname',
            'SFA_PLC_URL' : 'deferred-myplc-api-url',
            'SFA_PLC_USER' : 'root@test.onelab.eu',
            'SFA_PLC_PASSWORD' : 'test++',
# use -c sfadebug to increment this one
            'SFA_API_LOGLEVEL': 1,
# use -c sfavoid to set this to 'void'
            'SFA_GENERIC_FLAVOUR' : 'pl',
            'SFA_AGGREGATE_ENABLED' : 'true',
        },
        # details of the slices to create
        'auth_sfa_specs' : [ test_auth_sfa_spec(options, index) ]
    }

# rspec_style used to be 'pl' for sfav1 or 'pg' for pgv2 - OBSOLETE
def test_auth_sfa_spec (options, index):
    domain = pldomain
    # the auth/site part per se
    login_base = sfa_login_base(index)
    hrn_prefix = '{}.{}'.format(sfa_root(index),login_base)
    def full_hrn(x):  return "{}.{}".format(hrn_prefix,x)
    def full_mail(x): return "{}@test.{}".format(x,domain)

    # 2 users; we use dashes on purpose, as it might show up in email addresses
    pi_alias = 'pi-user'
    user_alias = 'regular-user'
#    pi_alias = 'pi'
#    user_alias = 'user'
    # 
    pi_spec = {
        'name':         pi_alias,
        'email':        full_mail (pi_alias),
        'key_name':     'key_sfapi',
        }
    user_spec = {
        'name':         user_alias,
        'email':        full_mail (user_alias),
        'key_name':     'key_sfauser',
        'register_options':  [ '--extra',"first_name=Fake",
                               '--extra',"last_name=SFA",
                          ],
        'update_options': [ '--extra',"enabled=true",
                             ],
        }

    slice_spec = {
        'name':          'sl',
        'register_options':  [ '--researchers', full_hrn (user_alias),
                               '--extra', "description=SFA-testing",
                               '--extra', "url=http://slice{}.test.onelab.eu/".format(index),
                               '--extra', "max_nodes=2",
                          ],
        'key_name':    'key_sfauser',
        'nodenames':    all_nodenames(options, index),
        }
        
    # we're already in a dedicated site/authority so no need to encumber with odd names

    return { 
             'login_base' : login_base,
             'domain'     : domain,
             'pi_spec'    : pi_spec,
             'user_spec'  : user_spec,
             'slice_spec' : slice_spec,
             } 


def config (plc_specs, options):
    result = plc_specs
    # plc 'index' starts with 1 
    for i in range(options.size):
        result.append(plc(options, i+1))
    return result

### for creating a sample config interactively
def sample_test_plc_spec ():
    class Void: pass

    options = Void()
    options.size = 1

    return config([], options)[0]

if __name__ == '__main__':
    s = sample_test_plc_spec()
    print('Sample plc_spec has the following keys')
    for k in sorted(s.keys()):
        print(k)
