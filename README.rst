Auto Configuration of Target and Host Computer for ROS development
=======================================================================

Target computer is a Gumstix and I am using Fabric as a auto configuration tool.
Before you run the command, you have to configure ``fab.conf``
with your correct information.

::

    $ fab -c fab.conf devel set_hosts
    $ fab -c fab.conf overo set_hosts
    $ fab -c fab.conf devel cp_overo_roscore
    $ fab -c fab.conf overo set_overo_mlan

    
