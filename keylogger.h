#define KBD_INT 1

#define LSHIFT_ON 	0x2A
#define RSHIFT_ON 	0x36
#define LSHIFT_OFF 	0xAA
#define RSHIFT_OFF 	0xB6
#define CAPS_ON		0x3A
#define CAPS_OFF	0xBA

#define CONTROL_CODE 	5
#define NEW_CHARACTER	6


static int capslock_on = 0;
static int shift_on = 0;

/** Takes in a scancode and destination for a char
  * Returns CONTROL_CODE if the scancode indicates shift or capslock being turned on or off
  * Otherwise, returns NEW_CHARACTER and looks up the character to set dest to in a lookup table
  */
int handle_scancode(unsigned char scancode, char *dest);
