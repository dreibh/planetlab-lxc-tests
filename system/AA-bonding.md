# bonding

Say you have 

* one build `2015.04.13--f14` under test
* another build `2015.04.13--f18` that you would like to use to create f18 nodes inside 	`2015.04.13--f14`

general idea is to use this command

	root@testmaster ~/2015.04.13--f14 # run -g 2015.04.13--f18 ...
	
or in an equivalent manner

	export bonding=bond212015.04.13--f18
	run -G
	
# requirements

* the build to test (f14) must be running
* the build to bond with does not need to run but needs to be have run under `../2015.04.13--f18` so that its arg-* files reflect its flavour

# convenience

* rung can be used as a symlink to `TestMain.py`
* in this case it is like running `run -G`

* plus, `comp-testmaster` offers the convenience function
		
		bond ../$(t)*18
		
* or, even simpler

		bond18		

# initialisation

	bond18
	rung
    
will define the f18 node flavour to the f14 build
 
# creating bonding node

	rung nodes

will create an additional node in tested myplc. 

**NOTE** for efficiency the IP and hostname of that node are stored in `arg-bonding-$bonding`

# starting node

as a matter of fact when doing `run -g $bonding` one can invoke most of the usual targets, including for starting the node

	rung start-node wait-node
	
# usual sequence

	alias rung='run -g $bonding'
	bonding=2015.04.13--f21
	rung 
	rung -n bonding-node
	cat arg-bonding-$bonding
	<<visual check>>
	rung bonding-node


# upgrading nodes

targets like `nodedistro-f22` can be used to change a node's fcdistro


## testing upgrade (one node)

testing a node upgrade; we start from a f21 myplc and upgrade the node to f22

### Init

    f21
    bond22
    rung
    run nodeplain-off

### Upgrade the node (make sure nodeplain is off)
    
    run nodedistro-f22 nodestate-upgrade
    run reset-node wait-node
    
### Reinstall - back to square 1

	run nodedistro-f21 nodestate-reinstall
	run reset-node wait-node
    
### Run bootmanager interactively during upgrade
To deploy experimental bootmanager code:

* Insert breakpoints in the bootmanager code
* turn on `BREAKPOINT_MODE = True` in `utils.py`
* `make sync` 

Then 

    run nodedistro-f22 nodestate-safeboot 
    run reset-node ssh-node-debug
    testnodedbg
    
    cd /tmp/source
    ./BootManager.py upgrade
    
	
