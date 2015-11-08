#include <linux/kernel.h>
#include <linux/interrupt.h>
#include <asm/io.h>

#define KBD_INT 1

#define LSHIFT_ON 	0x2A
#define RSHIFT_ON 	0x36
#define LSHIFT_OFF 	0xAA
#define RSHIFT_OFF 	0xB6
#define CAPS_ON		0x3A
#define CAPS_OFF	0xBA

#define CONTROL_CODE 	5
#define NEW_CHARACTER	6


static int cap_on = 0;

int handle_scancode(unsigned char scancode, char *dest)
{
	if(scancode == LSHIFT_ON || scancode == RSHIFT_ON || scancode == CAPS_ON) {
		cap_on = 1;
		return CONTROL_CODE;

	} else if(scancode == LSHIFT_OFF || scancode == RSHIFT_OFF || scancode == CAPS_OFF) {
		cap_on = 0;
		return CONTROL_CODE;
	}
}

/*
 This function services keyboard interrupts.
*/
irq_handler_t irq_handler (int irq, void *dev_id, struct pt_regs *regs)
{
	static unsigned char scancode;
	int reslt;
	char c;
	/*
	 Read keyboard status
	*/
	scancode = inb (0x60);

	// handle the scancode
	reslt = handle_scancode(scancode, &c);
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
