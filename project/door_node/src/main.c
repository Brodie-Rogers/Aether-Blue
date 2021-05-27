/**
************************************************************
* @file     p3/mobile/src/main.c
* @author   Brodie Rogers - 45299823
* @author   Riley Norris - 44781796
* @date     28/03/2021
* @brief    'Door' node for project
************************************************************
**/

#include <zephyr/types.h>
#include <stddef.h>
#include <sys/util.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <stdio.h>
#include <sys/printk.h>

#include <sys/util.h>
#include <string.h>
#include <usb/usb_device.h>
#include <drivers/uart.h>
#include <devicetree.h>
#include <drivers/gpio.h>

#define ID_1 0xab
#define ID_2 0xc1 
#define NODE_NUM 5

//Globals
int led_on = 1;
int prev_time = 0;


//LED defines
#define LED0_NODE   DT_ALIAS(led2)
#define GREEN_LED_PIN     DT_GPIO_PIN(LED0_NODE, gpios)
#define GREEN_LED	    DT_GPIO_LABEL(LED0_NODE, gpios)
#define FLAGS0	DT_GPIO_FLAGS(LED0_NODE, gpios)

#define LED1_NODE   DT_ALIAS(led1)
#define RED_LED_PIN     DT_GPIO_PIN(LED1_NODE, gpios)
#define RED_LED	    DT_GPIO_LABEL(LED1_NODE, gpios)
#define FLAGS1	DT_GPIO_FLAGS(LED1_NODE, gpios)

//LED structs
const struct device *red_led; 
const struct device *green_led; 


/**
**Scan callback for when bt data recieved
**/
static void scan_cb(const bt_addr_le_t *addr, int8_t rssi, uint8_t adv_type,
		    struct net_buf_simple *buf) {

	int ID = ((buf->data)[1]) << 8 | ((buf->data)[2]);
	int node = (buf->data)[3];

    if (ID == 0xabc1){

        if (node == 0xFF){

            if ((buf->data)[4] == 'o') {
				gpio_pin_set(red_led, RED_LED_PIN, 0);
				gpio_pin_set(green_led, GREEN_LED_PIN, 1);
				

			} else if ((buf->data)[4] == 'f') {
				gpio_pin_set(red_led, RED_LED_PIN, 1);
				gpio_pin_set(green_led, GREEN_LED_PIN, 0);
				
            }
        }
    }
}


/**
 * Main function
 */
void main(void) {

    int err;
    red_led = device_get_binding(RED_LED);
	green_led = device_get_binding(GREEN_LED);
    gpio_pin_configure(red_led, RED_LED_PIN, GPIO_OUTPUT_INACTIVE | FLAGS1);  
	gpio_pin_configure(green_led, GREEN_LED_PIN, GPIO_OUTPUT_ACTIVE | FLAGS0);  

	const struct device* dev = device_get_binding(
			CONFIG_UART_CONSOLE_ON_DEV_NAME);
	uint32_t dtr = 0;

    if (usb_enable(NULL)) {
		return;
	}

	struct bt_le_scan_param scan_param = {
		.type       = BT_HCI_LE_SCAN_PASSIVE,
		.options    = BT_LE_SCAN_OPT_NONE,
		.interval   = 0x0010,
		.window     = 0x0010,
	};

	err = bt_enable(NULL);

	err = bt_le_scan_start(&scan_param, scan_cb);

    while(1) {
		k_sleep(K_SECONDS(1));
    }

}
