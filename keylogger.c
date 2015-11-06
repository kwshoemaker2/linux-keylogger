#include <linux/kernel.h>
#include <linux/interrupt.h>
#include <asm/io.h>

#define KBD_INT 1

char to_character(unsigned char scancode)
{
	switch(scancode)
	{
		case 0x1E:
			return 'a';

		case 0x30:
			return 'b';

		case 0x2E:
			return 'c';

		case 0x20:
			return 'd';

		case 0x12:
			return 'e';

		case 0x21:
			return 'f';

		case 0x22:
			return 'g';

		case 0x23:
			return 'h';

		case 0x17:
			return 'i';

		case 0x24:
			return 'j';

		case 0x25:
			return 'k';

		case 0x26:
			return 'l';

		case 0x32:
			return 'm';

		case 0x31:
			return 'n';

		case 0x18:
			return 'o';

		case 0x19:
			return 'p';

		case 0x10:
			return 'q';

		case 0x13:
			return 'r';

		case 0x1F:
			return 's';

		case 0x14:
			return 't';

		case 0x16:
			return 'u';

		case 0x2F:
			return 'v';

		case 0x11:
			return 'w';
			
		case 0x2D:
			return 'x';

		case 0x15:
			return 'y';

		case 0x2C:
			return 'z';

		default:
			return '\0';
	}
}

/*
 This function services keyboard interrupts.
*/
irq_handler_t irq_handler (int irq, void *dev_id, struct pt_regs *regs)
{
	static unsigned char scancode;
	char c;
	/*
	 Read keyboard status
	*/
	scancode = inb (0x60);
	c = to_character(scancode);
	if(c != '\0') {
		printk("\n%c was pressed", c);
	
	} else {
		printk ("\nYou pressed: %x", scancode);
	}

	return (irq_handler_t) IRQ_HANDLED;
}

/*
 Initialize the module - register the IRQ handler
*/
int init_module (void)
{
	int result;
	/*
 	 Request IRQ 1, the keyboard IRQ, to go to our irq_handler SA_SHIRQ means we're willing to have othe handlers on this IRQ. SA_INTERRUPT can be used to make the handler into a fast interrupt.
	*/
	result = request_irq (KBD_INT, (irq_handler_t) irq_handler, IRQF_SHARED, "test_keyboard_irq_handler", (void *)(irq_handler));
	return result;
}

//MODULE_LICENSE ("GPL");
