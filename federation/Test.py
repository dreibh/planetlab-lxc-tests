#!/usr/bin/python
#
# Test script for peer caching
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

"""
Test script for peer caching. Intended for testing multiple PLCs
running on the same machine in different chroots. Here is how I set
things up after installing and configuring MyPLC:

# Shut down MyPLC
service plc stop

# Copy to /plc2
cp -ra /plc /plc2
ln -sf plc /etc/init.d/plc2
echo 'PLC_ROOT=/plc2/root' > /etc/sysconfig/plc2
echo 'PLC_DATA=/plc2/data' >> /etc/sysconfig/plc2

# Edit /plc2/data/etc/planetlab/plc_config.xml and change at least the
# following so that they do not conflict with the defaults:
#
# PLC_NAME (e.g., PlanetLab Two)
# PLC_SLICE_PREFIX (e.g., two)
# PLC_ROOT_USER (e.g., root@planetlab.two)
# PLC_API_MAINTENANCE_USER (e.g., maint@planetlab.two)
# PLC_DB_PORT (e.g., 5433)
# PLC_WWW_PORT (e.g., 81)
# PLC_WWW_SSL_PORT (e.g., 444)
# PLC_API_PORT (must be the same as PLC_WWW_SSL_PORT, e.g., 444)
# PLC_BOOT_SSL_PORT (must be the same as PLC_WWW_SSL_PORT, e.g., 444)
# PLC_BOOT_PORT (may be the same as PLC_WWW_PORT, e.g., 81)

# Start up both MyPLC instances
service plc start
service plc2 start

# Run test
./Test.py -f /etc/planetlab/plc_config -f /plc2/data/etc/planetlab/plc_config

# If the test fails and your databases are corrupt and/or you want to
# start over, you can always just blow the databases away.
service plc stop
rm -rf /plc/data/var/lib/pgsql/data
service plc start

service plc2 stop
rm -rf /plc2/data/var/lib/pgsql/data
service plc2 start
"""

import re
from optparse import OptionParser

from PLC.Config import Config
from PLC.GPG import gpg_export
from PLC.Shell import Shell
from PLC.Test import Test

def todict(list_of_dicts, key):
    """
    Turn a list of dicts into a dict keyed on key.
    """

    return dict([(d[key], d) for d in list_of_dicts])

def RefreshPeers(plcs):
    """
    Refresh each peer with each other.
    """

    for plc in plcs:
        for peer in plcs:
            if peer == plc:
                continue

            print plc.config.PLC_NAME, "refreshing", peer.config.PLC_NAME
            plc.RefreshPeer(peer.config.PLC_NAME)

            peer_id = plc.GetPeers([peer.config.PLC_NAME])[0]['peer_id']

            peer_sites = todict(plc.GetSites({'peer_id': peer_id}), 'site_id')
            sites_at_peer = todict(peer.GetSites(), 'site_id')

            peer_keys = todict(plc.GetKeys({'peer_id': peer_id}), 'key_id')
            keys_at_peer = todict(peer.GetKeys(), 'key_id')

            peer_persons = todict(plc.GetPersons({'peer_id': peer_id}), 'person_id')
            persons_at_peer = todict(peer.GetPersons(), 'person_id')

            peer_nodes = todict(plc.GetNodes({'peer_id': peer_id}), 'node_id')
            nodes_at_peer = todict(peer.GetNodes(), 'node_id')

            our_nodes = todict(plc.GetNodes({'peer_id': None}), 'node_id')
            our_peer_id_at_peer = peer.GetPeers([plc.config.PLC_NAME])[0]['peer_id']
            our_nodes_at_peer = todict(peer.GetNodes({'peer_id': our_peer_id_at_peer,
                                                      'peer_node_id': our_nodes.keys()}), 'peer_node_id')

            peer_slices = todict(plc.GetSlices({'peer_id': peer_id}), 'peer_slice_id')
            slices_at_peer = todict(peer.GetSlices(), 'slice_id')
 
            for site_id, site in peer_sites.iteritems():
                # Verify that this site exists at the peer
                peer_site_id = site['peer_site_id']
                assert peer_site_id in sites_at_peer
                peer_site = sites_at_peer[peer_site_id]

                # And is the same
                for field in ['name', 'abbreviated_name', 'login_base', 'is_public',
                              'latitude', 'longitude', 'url',
                              'max_slices', 'max_slivers',]:
                    assert site[field] == peer_site[field]

            for key_id, key in peer_keys.iteritems():
                # Verify that this key exists at the peer
                peer_key_id = key['peer_key_id']
                assert peer_key_id in keys_at_peer
                peer_key = keys_at_peer[peer_key_id]

                # And is the same
                for field in ['key_type', 'key']:
                    assert key[field] == peer_key[field]

            for person_id, person in peer_persons.iteritems():
                # Verify that this user exists at the peer
                peer_person_id = person['peer_person_id']
                assert peer_person_id in persons_at_peer
                peer_person = persons_at_peer[peer_person_id]

                # And is the same
                for field in ['first_name', 'last_name', 'title', 'email', 'phone',
                              'url', 'bio', 'enabled']:
                    assert person[field] == peer_person[field]

                for key_id in person['key_ids']:
                    # Verify that the user is not associated with any local keys
                    assert key_id in peer_keys
                    key = peer_keys[key_id]
                    peer_key_id = key['peer_key_id']

                    # Verify that this key exists at the peer
                    assert peer_key_id in keys_at_peer
                    peer_key = keys_at_peer[peer_key_id]

                    # And is related to the same user at the peer
                    assert peer_key['key_id'] in peer_person['key_ids']

            for node_id, node in peer_nodes.iteritems():
                # Verify that this node exists at the peer
                peer_node_id = node['peer_node_id']
                assert peer_node_id in nodes_at_peer
                peer_node = nodes_at_peer[peer_node_id]

                # And is the same
                for field in ['boot_state', 'ssh_rsa_key', 'hostname',
                              'version', 'model']:
                    assert node[field] == peer_node[field]

                # Verify that the node is not associated with any local sites
                assert node['site_id'] in peer_sites
                site = peer_sites[node['site_id']]

                # Verify that this site exists at the peer
                peer_site_id = site['peer_site_id']
                assert peer_site_id in sites_at_peer
                peer_site = sites_at_peer[peer_site_id]

                # And is related to the same node at the peer
                assert peer_site['site_id'] == peer_node['site_id']

            for slice_id, slice in peer_slices.iteritems():
                # Verify that this slice exists at the peer
                peer_slice_id = slice['peer_slice_id']
                assert peer_slice_id in slices_at_peer
                peer_slice = slices_at_peer[peer_slice_id]

                # And is the same
                for field in ['name', 'instantiation', 'url', 'description',
                              'max_nodes', 'expires']:
                    assert slice[field] == peer_slice[field]

                for node_id in slice['node_ids']:
                    # Verify that the slice is associated only with
                    # the peer's own nodes, or with our nodes as
                    # last cached by the peer.
                    assert node_id in peer_nodes or node_id in our_nodes_at_peer
                    if node_id in peer_nodes:
                        node = peer_nodes[node_id]
                        peer_node_id = node['peer_node_id']
                    elif node_id in our_nodes_at_peer:
                        peer_node = our_nodes_at_peer[node_id]
                        peer_node_id = peer_node['node_id']

                    # Verify that this node exists at the peer
                    assert peer_node_id in nodes_at_peer

                    # And is related to the same slice at the peer
                    assert peer_node_id in peer_slice['node_ids']

def TestPeers(plcs, check = True, verbose = True, tiny = False):
    # Register each peer with each other
    for plc in plcs:
        for peer in plcs:
            if peer == plc:
                continue

            key = gpg_export(peer.chroot + peer.config.PLC_ROOT_GPG_KEY_PUB)
            cacert = file(peer.chroot + peer.config.PLC_API_CA_SSL_CRT).read()

            if plc.GetPeers([peer.config.PLC_NAME]):
                print plc.config.PLC_NAME, "updating peer", peer.config.PLC_NAME
                plc.UpdatePeer(peer.config.PLC_NAME,
                               {'peer_url': peer.url, 'key': key, 'cacert': cacert})
            else:
                print plc.config.PLC_NAME, "adding peer", peer.config.PLC_NAME
                plc.AddPeer({'peername': peer.config.PLC_NAME,
                             'peer_url': peer.url, 'key': key, 'cacert': cacert})

        # Populate the DB
        plc.test = Test(api = plc, check = check, verbose = verbose)

        if tiny:
            params = Test.tiny
        else:
            params = Test.default

        print "Populating", plc.config.PLC_NAME
        plc.test.Add(**params)

    # Refresh each other
    RefreshPeers(plcs)

    # Change some things
    for plc in plcs:
        print "Updating", plc.config.PLC_NAME
        plc.test.Update()

    # Refresh each other again
    RefreshPeers(plcs)

def main():
    parser = OptionParser()
    parser.add_option("-f", "--config", dest = "configs", action = "append", default = [], help = "Configuration file (default: %default)")
    parser.add_option("-c", "--check", action = "store_true", default = False, help = "Verify actions (default: %default)")
    parser.add_option("-q", "--quiet", action = "store_true", default = False, help = "Be quiet (default: %default)")
    parser.add_option("-t", "--tiny", action = "store_true", default = False, help = "Run a tiny test (default: %default)")
    (options, args) = parser.parse_args()

    # Test single peer by default
    if not options.configs:
        options.configs = ["/etc/planetlab/plc_config"]

    plcs = []
    for path in options.configs:
        # Load configuration file
        config = Config(path)

        # Determine path to chroot
        m = re.match(r'(.*)/etc/planetlab', path)
        if m is not None:
            chroot = m.group(1)
        else:
            chroot = ""

        # Fix up path to SSL certificate
        cacert = chroot + config.PLC_API_CA_SSL_CRT

        # Always connect with XML-RPC
        plc = Shell(config = path, cacert = cacert, xmlrpc = True)
        plc.chroot = chroot
        plcs.append(plc)

    TestPeers(plcs, check = options.check, verbose = not options.quiet, tiny = options.tiny)

if __name__ == "__main__":
    main()
