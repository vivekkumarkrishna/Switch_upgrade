# import of all the required libraries

from netmiko import ConnectHandler
from datetime import datetime
from netmiko import file_transfer
import re, time, sys


# put the cisco file image
# Cisco_IOS = "cat3k_caa-universalk9.16.12.07.SPA.bin"
switch_list = []
# Reading the list of ip and storing in the Switch_list
with open('switch_list.txt') as file:
    for line in file:
        line=line.rstrip()
        switch_list.append(line)

#clearing the old data from the CSV file and writing the headers
f = open("pre_upgrade.csv", "w+")
f.write("IP Address, Hostname, Device_Model, Current_Image")
f.write("\n")
f.close()

#Opening teh CSV file and writing the headers for Post upgrade
f = open("post_upgrade.csv", "w+")
f.write("IP Address, Hostname, Device_Model, Current_Image")
f.write("\n")
f.close()

# pre upgrade task to Collect iso, modal, and copy the file and set boot variable reload action
def pre_upgrade(ip_list,username,password,iso_file):
    for ip in ip_list:
        cisco = {
            'device_type': 'cisco_ios_telnet',
            'ip': ip,
            'username': username,  # ssh username
            'password': password,  # ssh password
            'secret': password,  # ssh_enable_password
            'fast_cli': False,
            'allow_auto_change' : False
        }
        net_connect = ConnectHandler(**cisco)
        pre_upgrade_devices = []
        sh_ver_output = net_connect.send_command('show version')
        hostname=net_connect.find_prompt().strip("#").strip(">")

        # sample line to be extracted 'A_StubR uptime is 25 minutes'
        # finding model in output using regular expressions
        regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
        model = regex_model.findall(sh_ver_output)

        # finding ios image in output using regular expressions
        # sample line to be extracted 'System image file is “flash:c2500-js-l_113-6.bin”, booted via flash'
        regex_ios = re.compile(r'System\simage\sfile\sis\s"([^ "]+)')
        ios = regex_ios.findall(sh_ver_output)

        # append results to table [hostname,uptime,version,serial,ios,model]
        pre_upgrade_devices.append([ip, hostname[0], model[0], ios[0]])

        transfer_dict = file_transfer(
            net_connect,
            source_file=iso_file,
            dest_file=iso_file,
            file_system='bootflash',
            direction='put',
            overwrite_file=True,
        )
        print(transfer_dict)

        # Enter the New IOS#
        remove_boot = "no boot system"
        remove_boot = net_connect.send_config_set(remove_boot)
        add_boot = "boot system flash:" + iso_file
        add_boot = net_connect.send_config_set(add_boot)
        write_config = net_connect.send_command_timing("wr mem", strip_prompt=False, strip_command=False, delay_factor=2)
        confirm_reload = net_connect.send_command('reload', expect_string='[confirm]')
        confirm_reload = net_connect.send_command('\n', expect_string='[confirm]')
        now = datetime.now()
reload_wait_time = "300"
def sleeptime():
    now = datetime.now()
    logs_time = now.strftime("%H:%M:%S")
    print("" + logs_time + ": Wait time activated, please wait for " + str(reload_wait_time) + " seconds")
    time.sleep(int(reload_wait_time))


def post_upgrade(ip_list,username,password):
    for ip in ip_list:
        cisco = {
            'device_type': 'cisco_ios_telnet',
            'ip': ip,
            'username': username,  # ssh username
            'password': password,  # ssh password
            'secret': password,  # ssh_enable_password
            'fast_cli': False,
            'allow_auto_change': False
        }
        net_connect = ConnectHandler(**cisco)
        post_upgrade_devices = []
        sh_ver_output = net_connect.send_command('show version')
        hostname = net_connect.find_prompt().strip("#").strip(">")

        # sample line to be extracted 'A_StubR uptime is 25 minutes'
        # finding model in output using regular expressions
        regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
        model = regex_model.findall(sh_ver_output)

        # finding ios image in output using regular expressions
        # sample line to be extracted 'System image file is “flash:c2500-js-l_113-6.bin”, booted via flash'
        regex_ios = re.compile(r'System\simage\sfile\sis\s"([^ "]+)')
        ios = regex_ios.findall(sh_ver_output)

        # append results to table [hostname,uptime,version,serial,ios,model]
        post_upgrade_devices.append([ip, hostname[0], model[0], ios[0]])

        # print all results (for all routers) on screen
        for i in post_upgrade_devices:
            i = ", ".join(i)
            f = open("pre_upgrade.csv", "a")
            f.write(i)
            f.write("\n")
            f.close()

if __name__ == "__main__":

    no_arg = len(sys.argv)
    if no_arg==4:
        username = sys.argv[1]
        password = sys.argv[2]
        iso_file = sys.argv[3]
        ip_list = switch_list
        pre_upgrade(ip_list, username, password, iso_file)
        sleeptime()
        post_upgrade(ip_list, username, password)
    else:

        print('Please run the Script With correct argument example Below')
        print('python Switch_upgrade.py username password cisco_iso_filename')





