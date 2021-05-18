/**
************************************************************
* @file     project/base/src/main.c
* @author   Brodie Rogers - 45299823
* @author   Riley Norris - 44781796
* @date     17/05/2021
* @brief    Main file for p3 base node
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

#define ID_1 0xab
#define ID_2 0xc1 
#define NODE_NUM 5



int previous_1[6] = {0,0,0,0,0,0};
bool new_data_1 = true;

int previous_2[6] = {0,0,0,0,0,0};
bool new_data_2 = true;



/**
**Scan callback for when bt data recieved. This is the data that is received
** by each mobile then forwarded here to the base node, which then gives that
** data to the python script.
**/
static void scan_cb(const bt_addr_le_t *addr, int8_t rssi, uint8_t adv_type,
		    struct net_buf_simple *buf)
{

	int ID = ((buf->data)[1]) << 8 | ((buf->data)[2]);
	int co2_1;
	int co2_2;
	int tvoc_1;
	int tvoc_2;

	int node = (buf->data)[3];
    //Checking to see if received is one of the mobile node IDs
    if (ID == 0xabc1) {

		for (int i = 0; i < 8; i++){
			printk("--%X--", buf->data[i]);

		}
		printk("\n");

		if (node == 1){
			for (int i = 0; i < 8; i++){
				if (previous_1[i] != (buf->data)[i]){
					new_data_1 = true;
				}
			}

			if(new_data_1){

				for (int i = 0; i < 8; i++) {

					previous_1[i] = (buf->data)[i];
					//printk("--%X--", (buf->data)[i]);
				}

				co2_1 = ((buf->data)[4] << 8) | ((buf->data)[5]);
				tvoc_1 = ((buf->data)[6] << 8) | ((buf->data)[7]);
				printk("#B3;%d,%d;%d,%d!\n\r", co2_1, co2_2, tvoc_1, tvoc_2);
				//printk("\n");
				new_data_1 = false;
			}

		} else if(node ==2) {

			for (int i = 0; i < 8; i++) {

				if (previous_2[i] != (buf->data)[i]) {
					new_data_2 = true;
				}
			}

			if(new_data_2){

				for (int i = 0; i < 8; i++) {

					previous_2[i] = (buf->data)[i];
					//printk("--%X--", (buf->data)[i]);
				}

				co2_2 = ((buf->data)[4] << 8) | ((buf->data)[5]);
				tvoc_2 = ((buf->data)[6] << 8) | ((buf->data)[7]);
				printk("#B3;%d,%d;%d,%d!\n\r", co2_1, co2_2, tvoc_1, tvoc_2);
				//printk("\n");
				new_data_2 = false;
			}

		}
	}
}



/**
 * Main function
 */
void main(void) {


    //Setting up bluetooth for base to receive from mobile
    int err;
	const struct device* dev = device_get_binding(
			CONFIG_UART_CONSOLE_ON_DEV_NAME);
	

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
