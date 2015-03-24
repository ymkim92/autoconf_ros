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
    my_ipaddress = socket.gethostbyname(socket.gethostname())
    change_etc_hosts(my_ipaddress, my_hostname)
    change_etc_hosts(env.overo_ipaddress, 'overo')

def cp_overo_roscore():
    # after devel

    roscore_file_name = 'conf/roscore'
    my_hostname = socket.gethostname()
    generate_roscore(my_hostname, roscore_file_name)
    call(['scp', roscore_file_name, 'root@overo:/etc/default/roscore']) 

def fix_rosserial_path():
    # after overo

    # TODO: I couldn't understand why this has to be done
    run("ln -s /usr/lib/rosserial_python/serial_node.py /usr/share/rosserial_python/serial_node.py")

def set_overo_rosserial():
    # after overo

    mlan_file_name = 'conf/rosserial.service'
    call(['scp', mlan_file_name, 'root@overo:/etc/systemd/system']) 
    run("systemctl enable rosserial.service")

def set_overo_mlan():
    # after overo
    
    mlan_file_name = 'conf/wpa_supplicant-mlan0.conf'
    call(['scp', mlan_file_name, 'root@overo:/etc/wpa_supplicant']) 

    # /lib/systemd/system/udhcpc\@.service
    udhcpc_file_name = '/lib/systemd/system/udhcpc\@.service'
    run("/bin/sed -i.bak 's/IFACE/mlan0/' %s" %udhcpc_file_name)
    run("systemctl enable udhcpc@mlan0")
    run("systemctl enable wpa_supplicant@mlan0")

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

