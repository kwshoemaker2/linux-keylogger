#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/interrupt.h>
#include <linux/proc_fs.h>
#include <linux/string.h>

#define PROC_FILE_NAME "kylgr"
#define BUFFER_SIZE 1024 * 1024

char buffer[BUFFER_SIZE];

ssize_t read_simple(struct file *filp, char *buf, size_t count, loff_t *offp )
{
	buffer[0] = 'A';
	copy_to_user(buf, buffer, count);
	memset(buffer, 0, BUFFER_SIZE);
	return count;
}


struct file_operations proc_fops = {
	read: read_simple
};

int __init keylogger_init(void)
{
	proc_create(PROC_FILE_NAME, 0, NULL, &proc_fops);
	return 0;
}

void __exit keylogger_exit(void)
{

}

MODULE_LICENSE("GPL");
module_init(keylogger_init);
module_exit(keylogger_exit);
