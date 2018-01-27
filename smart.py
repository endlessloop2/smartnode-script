#! /usr/bin/env python
from subprocess import Popen,PIPE,STDOUT
import collections
import os
import sys
import time
import math
import os
import time
from urllib2 import urlopen

BOOTSTRAP_URL = "http://proteanx.com/txindexstrap.zip"

MN_USERNAME = ""
MN_PORT = 9678
MN_RPCPORT = 9679 # https://github.com/SmartCash/smartcash/blob/1.1/src/chainparamsbase.cpp#L35
MN_NODELIST = ""

MN_LFOLDER = ".smartcash"
MN_WFOLDER = "Smartcash"
MN_CONFIGFILE = "smartcash.conf"
MN_DAEMON = "smartcashd"
MN_CLI = "smartcash-cli"
MN_EXPLORER = "https://explorer.smartcash.cc"

MN_SWAPSIZE = "2G"
SERVER_IP = urlopen('http://ip.42.pl/raw').read()
DEFAULT_COLOR = "\x1b[0m"
PRIVATE_KEY = ""

def print_info(message):
    BLUE = '\033[94m'
    print(BLUE + "[*] " + str(message) + DEFAULT_COLOR)
    time.sleep(1)

def print_warning(message):
    YELLOW = '\033[93m'
    print(YELLOW + "[*] " + str(message) + DEFAULT_COLOR)
    time.sleep(1)

def print_error(message):
    RED = '\033[91m'
    print(RED + "[*] " + str(message) + DEFAULT_COLOR)
    time.sleep(1)

def get_terminal_size():
    import fcntl, termios, struct
    h, w, hp, wp = struct.unpack('HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ,
        struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h
    
def remove_lines(lines):
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    for l in lines:
        sys.stdout.write(CURSOR_UP_ONE + '\r' + ERASE_LINE)
        sys.stdout.flush()

def run_command_as(user, command):
    run_command('su - {} -c "{}" '.format(user, command))

def run_command(command):
    out = Popen(command, stderr=STDOUT, stdout=PIPE, shell=True)
    lines = []
    
    while True:
        line = out.stdout.readline()
        if (line == ""):
            break
        
        # remove previous lines     
        remove_lines(lines)
        
        w, h = get_terminal_size()
        lines.append(line.strip().encode('string_escape')[:w-3] + "\n")
        if(len(lines) >= 9):
            del lines[0]

        # print lines again
        for l in lines:
            sys.stdout.write('\r')
            sys.stdout.write(l)
        sys.stdout.flush()

    remove_lines(lines) 
    out.wait()

def print_welcome():
    os.system('clear')
    GREEN = '\033[32m'
    print(GREEN + "  _____                             _       " + DEFAULT_COLOR)
    print(GREEN + " |_   _|__ _ __ _ __ __ _  ___ ___ (_)_ __  " + DEFAULT_COLOR)
    print(GREEN + "   | |/ _ \ '__| '__/ _` |/ __/ _ \| | '_ \ " + DEFAULT_COLOR)
    print(GREEN + "   | |  __/ |  | | | (_| | (_| (_) | | | | |" + DEFAULT_COLOR)
    print(GREEN + "   |_|\___|_|  |_|  \__,_|\___\___/|_|_| |_|" + DEFAULT_COLOR)
    print(GREEN + "                                            " + DEFAULT_COLOR)
    print_info("Smartnode installer v0.1")

def update_system():
    print_info("Updating the system...")
    run_command("apt-get update")
    run_command("apt-get upgrade -y")
    run_command("apt-get dist-upgrade -y")

def check_root():
    print_info("Check root privileges")
    user = os.getuid()
    if user != 0:
        print_error("This program requires root privileges.  Run as root user.")
        sys.exit(-1)

def secure_server():
    print_info("Securing server...")
    run_command("apt-get --assume-yes install ufw")
    run_command("ufw allow OpenSSH")
    run_command("ufw allow {}".format(MN_PORT))
    run_command("ufw default deny incoming")
    run_command("ufw default allow outgoing")
    run_command("ufw --force enable")

def setup_wallet():
    swap = raw_input("Create swap file? (y or n)")
    if swap == "y":
      print_info("Allocating swap...")
      run_command("fallocate -l {} /swapfile".format(MN_SWAPSIZE))
      run_command("chmod 600 /swapfile")
      run_command("mkswap /swapfile")
      run_command("swapon /swapfile")

      f = open('/etc/fstab','r+b')
      line = '/swapfile   none    swap    sw    0   0 \n'
      lines = f.readlines()
      if (lines[-1] != line):
          f.write(line)
          f.close()

    print_info("Installing useful programs...")
    run_command("apt-get -y --assume-yes install git zip iptables htop nano wget")
    print_info("Adding wallet repository...")
    run_command("apt-get -y install software-properties-common")
    run_command("sudo add-apt-repository ppa:smartcash/ppa")
    run_command("apt-get update")
    run_command("apt-get -y --assume-yes install smartcashd")

    print_info("Downloading wallet and installing dependencies...")
    run_command("apt-get -y --assume-yes install smartcashd")
    
def setup_masternode():
    print_info("Setting up masternode...")
    masternode_alias = raw_input("alias: ")
    global MN_USERNAME
    MN_USERNAME = masternode_alias
    SERVER_IP = raw_input("IP to use: ")
    run_command("useradd --create-home -G sudo {}".format(MN_USERNAME))
    
    print_info("Open your desktop wallet config file (%appdata%/{}/{}) and copy\n    your rpc username and password! If it is not there create one! E.g.:\n\trpcuser=[SomeUserName]\n\trpcpassword=[DifficultAndLongPassword]".format(MN_WFOLDER, MN_CONFIGFILE))
    rpc_username = raw_input("rpcuser: ")
    rpc_password = raw_input("rpcpassword: ")

    print_info("Open your wallet console (Tools => Debug Console) and create a new masternode private key: masternode genkey")
    masternode_priv_key = raw_input("masternodeprivkey: ")
    global PRIVATE_KEY
    PRIVATE_KEY = masternode_priv_key
    
    config = """rpcuser={}
rpcpassword={}
rpcallowip=127.0.0.1
rpcport={}
port={}
server=1
listen=1
daemon=1
logtimestamps=1
mnconflock=1
masternode=1
externalip={}:{}
masternodeprivkey={}
{}""".format(rpc_username, rpc_password, MN_RPCPORT, MN_PORT, SERVER_IP, MN_PORT, masternode_priv_key, MN_NODELIST)

    # creates folder structure
    run_command_as(MN_USERNAME, "mkdir -p /home/{}/{}/".format(MN_USERNAME, MN_LFOLDER))
    run_command_as(MN_USERNAME, "touch /home/{}/{}/{}".format(MN_USERNAME, MN_LFOLDER, MN_CONFIGFILE))
    
    print_info("Saving config file...")
    with open('/home/{}/{}/{}'.format(MN_USERNAME, MN_LFOLDER, MN_CONFIGFILE), 'w') as f:
        f.write(config)
        
    print_info("Downloading blockchain file...")#TODO
    filename = "blockchain.zip"
    run_command_as(MN_USERNAME, "cd && wget -O {} {}".format(filename, BOOTSTRAP_URL))
    
    print_info("Unzipping the file...")   
    run_command_as(MN_USERNAME, "cd && unzip {} -d {}".format(filename, MN_LFOLDER))
       
    os.system('su - {} -c "{}" '.format(MN_USERNAME, MN_DAEMON + ' -daemon -reindex'))
    print_warning("Masternode started syncing in the background...")

def crontab(job):
    p = Popen("crontab -l -u {} 2> /dev/null".format(MN_USERNAME), stderr=STDOUT, stdout=PIPE, shell=True)
    p.wait()
    lines = p.stdout.readlines()
    if job not in lines:
        print_info("Cron job doesn't exist yet, adding it to crontab")
        lines.append(job)
        p = Popen('echo "{}" | crontab -u {} -'.format(''.join(lines), MN_USERNAME), stderr=STDOUT, stdout=PIPE, shell=True)
        p.wait()


def autostart_masternode():
    job = "@reboot /usr/local/bin/{}\n".format(MN_DAEMON)
    crontab(job)
    
def end():

    mn_base_data = """
    Alias: {}
    IP: {}
    Private key: {}
    Transaction ID: [The transaction id of the deposit. 'masternode outputs']
    Transaction index: [The transaction index of the deposit. 'masternode outputs']
    --------------------------------------------------
"""

    mn_data = mn_base_data.format(MN_USERNAME,SERVER_IP + ":" + str(MN_PORT), PRIVATE_KEY)

    print('')
    print_info(
"""Masternodes setup finished!
    Wait until the masternode is fully synced. To check the progress login the 
    masternode account (su {}) and run the '{} getinfo' command to get
    the actual block number. Go to {} website to check 
    the latest block number or use your wallet. After the syncronization is done 
    add your masternode to your desktop wallet.

Masternode data:""".format(MN_USERNAME, MN_CLI, MN_EXPLORER) + mn_data)


def main():
    print_welcome()
    check_root()
    update_system()
    secure_server()
    setup_wallet()
    setup_masternode()
    autostart_masternode()
    end()

if __name__ == "__main__":
    main()
