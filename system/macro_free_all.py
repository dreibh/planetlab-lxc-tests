# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# a macro for releasing all local resources and cleanup trackers

"release local resources (stop vs, kill qemus, clean trackers)"

# no trackers anymore
sequence = [ 'vs_stop', 'qemu_kill_mine', ]

