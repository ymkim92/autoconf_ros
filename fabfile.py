from fabric.api import cd, env, prefix, run, task, sudo
import sys
from subprocess import check_output, call, Popen, PIPE
import socket

def both():
    env.hosts = ['localhost', 'overo']

def devel():
    env.hosts = ['localhost']
    env.password = '1234'

def overo():    
    env.user = 'root'
    env.password = ''
    env.hosts = ['overo']

def set_hosts():
    # after devel and overo 

    my_hostname = socket.gethostname()
    change_etc_hosts(env.my_ipaddress, my_hostname)
    change_etc_hosts(env.overo_ipaddress, 'overo')

def cp_overo_roscore():
    # after devel

    roscore_file_name = 'conf/roscore'
    call(['scp', roscore_file_name, 'root@overo:/etc/default/roscore']) 
    call(['scp', 'conf/ros_init.rc', 'root@overo:~']) 
    call(['scp', 'conf/run_serial.sh', 'root@overo:~']) 
    call(['scp', 'conf/ublox_gps.launch',
          'root@overo:/opt/ros/hydro/lib/ublox_gps']) 

def set_overo_rosserial():
    # after overo

    mlan_file_name = 'conf/rosserial.service'
    call(['scp', mlan_file_name, 'root@overo:/etc/systemd/system']) 
    run("systemctl enable rosserial.service")

# This is for Kernel 3.5 or 3.6. 
# In 3.17 version, the device name is changed to wlan0
# and it is simple to activate wlan0 editing only
# /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
def set_overo_mlan():
    # after overo
    
    mlan_file_name = 'conf/wpa_supplicant-mlan0.conf'
    call(['scp', mlan_file_name, 'root@overo:/etc/wpa_supplicant']) 

    # /lib/systemd/system/udhcpc\@.service
    udhcpc_file_name = '/lib/systemd/system/udhcpc\@.service'
    run("/bin/sed -i.bak 's/wlan0/mlan0/' %s" %udhcpc_file_name)
    run("systemctl enable udhcpc@mlan0")
    run("systemctl enable wpa_supplicant@mlan0")

#rpm_path_name = '/home/ymkim/devel/yoc1/build/tmp/deploy/rpm/armv7a_vfp_neon/'
rpm_path_name = '/home/ymkim/devel/yoc1/build/tmp/deploy/rpm/cortexa8hf_vfp_neon/'
post_name = '.cortexa8hf_vfp_neon.rpm'

def install_base_rpms():
    #after overo
    '''
    $ cp -a ros-ublox ~/devel/yoc1/poky/meta-ros/recipes-ros
    $ cd ~/devel/yoc1/poky/meta-ros/recipes-ros
    $ ln -s ~/devel/yocto/tyltrotor tyltrotor
    bitbake packagegroup-ros-comm sensor-msgs
    bitbake diagnostic-msgs
    bitbake rosserial-msgs 
    bitbake screen
    bitbake python-pyserial ublox-gps main-control
    '''

    rpm_file_names = [
        'main-control-1.0.0-r0.0',
    ]
    for file_name in rpm_file_names:
        call(['scp', "%s%s%s" %(rpm_path_name, file_name, post_name), 'root@overo:/tmp/']) 
        run("rpm -ivh /tmp/%s%s" %(file_name, post_name))

def install_main_control():
    rpm_file_name = '%smain-control-1.0.0-r0.0.cortexa8hf_vfp_neon.rpm' %rpm_path_name
    call(['scp', rpm_file_name, 'root@overo:~']) 
    run("rpm -ivh --replacepkgs /home/root/main-control-1.0.0-r0.armv7a_vfp_neon.rpm")
    #run("rpm -ivh main-control-1.0.0-r0.armv7a_vfp_neon.rpm")

#--------------------------------------------------------------------------------------

def generate_roscore(roscore_hostname, file_name):
    #/etc/default/roscore
    with open(file_name, 'w') as outfile:
        outfile.write('ROS_ROOT=/usr\n')
        outfile.write('ROS_PACKAGE_PATH=/usr/lib\n')
        outfile.write('ROS_MASTER_URI=http://%s:11311\n' %roscore_hostname)
        outfile.write('MAKE_PREFIX_PATH=/usr\n')

def change_etc_hosts(ipaddr, hostname):    
    try:
        ret_string = run("cat /etc/hosts | grep %s" %hostname)
        result = run("echo %s | wc -l" %ret_string)
    except:
        result = '0'

    if result == '1':
        # change IP address of hostname with ipaddress
        ip_addr = ret_string.split()[0]
        sudo ("/bin/sed -i.bak '/%s/ c %s\t%s' /etc/hosts" %(hostname, ipaddr, hostname))
    elif result == '0':
        # add new line with ipaddr and hostname
        sudo("/bin/sh -c 'echo %s\t%s >> /etc/hosts'" %(ipaddr,
                                                       hostname))
    else:
        sys.exit("There are multiple lines of hostname %s" %hostname)

