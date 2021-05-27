/**
************************************************************
* @file     project/base/src/main.c
* @author   Brodie Rogers - 45299823
* @author   Riley Norris - 44781796
* @date     28/05/2021
* @brief    Main file for project base node
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
#define NODE_NUM 0xFF

//USB device
const struct device* dev;

//Current and previous data states
int previous_1[8] = {0,0,0,0,0,0,0,0};
bool new_data_1 = true;

int previous_2[8] = {0,0,0,0,0,0,0,0};
bool new_data_2 = true;


//Global variables storing sensor data
int co2_1 = 0;
int co2_2 = 0;
int tvoc_1 = 0;
int tvoc_2 = 0;
int baseline_1 = 5;
int baseline_2 = 5;

int temp1_whole;
int temp1_frac;
int temp2_whole;
int temp2_frac;

int hum1_whole;
int hum1_frac;
int hum2_whole;
int hum2_frac;



static uint8_t data[] = {ID_2 , NODE_NUM, 0x12, 0x12, 0x12, 0x12};

static const struct bt_data ad[] = {
	BT_DATA(ID_1, data, 9),
};

uint8_t recv_buffer[10];
uint8_t send_buffer[51] = {'#','B','3',';','0','0','0','0',',','0','0','0','0',';'
						,'0','0','0','0',',','0','0','0','0',';',
						'0','0','.','0','0',';','0','0','.','0','0',';',
						'0','0','.','0','0',';','0','0','.','0','0',';','!','\n','\r'};

void print_buffer(uint8_t* buf, int len) {

	uart_fifo_fill(dev, buf, len);
}

static void interrupt_handler(const struct device *dev, void *user_data)
{
	ARG_UNUSED(user_data);

	while (uart_irq_update(dev) && uart_irq_is_pending(dev)) {
		if (uart_irq_rx_ready(dev)) {

			int recv_len;
			recv_len = uart_fifo_read(dev, recv_buffer, 10);

			if (recv_buffer[0] == 'o' || recv_buffer[0] == 'f') {

				data[2] = recv_buffer[0];
				bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad), NULL, 0);
				k_msleep(500);
				bt_le_adv_stop();
				print_buffer(recv_buffer, recv_len);
			}
		}
	}
}


/**
 * Convert int to char
 */
uint8_t int_to_char(int num){
	return num + 48;
}



/**
 * Manually form UART message to send to PC Node:
 */
void print_to_serial(void) {

	send_buffer[4] = int_to_char(co2_1 / 1000);
	send_buffer[5] = int_to_char((co2_1 % 1000) / 100);
	send_buffer[6] = int_to_char((co2_1 % 100) / 10);
	send_buffer[7] = int_to_char((co2_1 % 10));

	send_buffer[9] = int_to_char(co2_2 / 1000);
	send_buffer[10] = int_to_char((co2_2 % 1000) / 100);
	send_buffer[11] = int_to_char((co2_2 % 100) / 10);
	send_buffer[12] = int_to_char((co2_2 % 10));

	send_buffer[14] = int_to_char(tvoc_1 / 1000);
	send_buffer[15] = int_to_char((tvoc_1 % 1000) / 100);
	send_buffer[16] = int_to_char((tvoc_1 % 100) / 10);
	send_buffer[17] = int_to_char((tvoc_1 % 10));

	send_buffer[19] = int_to_char(tvoc_2 / 1000);
	send_buffer[20] = int_to_char((tvoc_2 % 1000) / 100);
	send_buffer[21] = int_to_char((tvoc_2 % 100) / 10);
	send_buffer[22] = int_to_char((tvoc_2 % 10));

	send_buffer[24] = (temp1_whole / 10) + 48;
	send_buffer[25] = (temp1_whole % 10) + 48;
	
	send_buffer[27] = (temp1_frac / 10) + 48;
	send_buffer[28] = (temp1_frac % 10) + 48;

	send_buffer[30] = (hum1_whole / 10) + 48;
	send_buffer[31] = (hum1_whole % 10) + 48;

	send_buffer[33] = (hum1_frac / 10) + 48;
	send_buffer[34] = (hum1_frac % 10) + 48;

	send_buffer[36] = (temp2_whole / 10) + 48;
	send_buffer[37] = (temp2_whole % 10) + 48;
	
	send_buffer[39] = (temp2_frac / 10) + 48;
	send_buffer[40] = (temp2_frac % 10) + 48;

	send_buffer[42] = (hum2_whole / 10) + 48;
	send_buffer[43] = (hum2_whole % 10) + 48;

	send_buffer[45] = (hum2_frac / 10) + 48;
	send_buffer[46] = (hum2_frac % 10) + 48;


	// send_buffer[25] = int_to_char(baseline_1 / 10000);
	// send_buffer[26] = int_to_char(baseline_1 % 10000 / 1000);
	// send_buffer[27] = int_to_char((baseline_1 % 1000) / 100);
	// send_buffer[28] = int_to_char((baseline_1 % 100) / 10);
	// send_buffer[29] = int_to_char((baseline_1 % 10));

	// send_buffer[31] = int_to_char(baseline_2 / 10000);
	// send_buffer[32] = int_to_char(baseline_2 % 10000 / 1000);
	// send_buffer[33] = int_to_char((baseline_2 % 1000) / 100);
	// send_buffer[34] = int_to_char((baseline_2 % 100) / 10);
	// send_buffer[35] = int_to_char((baseline_2 % 10));




	uart_fifo_fill(dev, send_buffer, 40);
}



/**
**Scan callback for when bt data recieved. This is the data that is received
** by each mobile then forwarded here to the base node, which then gives that
** data to the python script.
**/
static void scan_cb(const bt_addr_le_t *addr, int8_t rssi, uint8_t adv_type,
		    struct net_buf_simple *buf)
{

	int ID = ((buf->data)[1]) << 8 | ((buf->data)[2]);

	int node = (buf->data)[3];
    //Checking to see if received is one of the mobile node IDs
    if (ID == 0xabc1) {

		if (node == 1){
			for (int i = 0; i < 8; i++){
				if (previous_1[i] != (buf->data)[i]){
					new_data_1 = true;
				}
			}

			if(new_data_1){

				for (int i = 0; i < 8; i++) {

					previous_1[i] = (buf->data)[i];

				}

				co2_1 = ((buf->data)[4] << 8) | ((buf->data)[5]);
				tvoc_1 = ((buf->data)[6] << 8) | ((buf->data)[7]);
				baseline_1 = ((buf->data)[8] << 8) | ((buf->data)[9]);
				temp1_whole = (buf->data)[10];
				temp1_frac = (buf->data)[11];
				hum1_whole = (buf->data)[12];
				hum1_frac = (buf->data)[13];
				new_data_1 = false;
				print_to_serial();
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
				}

				co2_2 = ((buf->data)[4] << 8) | ((buf->data)[5]);
				tvoc_2 = ((buf->data)[6] << 8) | ((buf->data)[7]);
				temp2_whole = (buf->data)[10];
				temp2_frac = (buf->data)[11];
				hum2_whole = (buf->data)[12];
				hum2_frac = (buf->data)[13];
				baseline_2 = ((buf->data)[8] << 8) | ((buf->data)[9]);
				print_to_serial();
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
	dev = device_get_binding("CDC_ACM_0");
	

    if (usb_enable(NULL)) {
		return;
	}

	uart_irq_callback_set(dev, interrupt_handler);

	/* Enable rx interrupts */
	uart_irq_rx_enable(dev);

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
		//print_to_serial();
    }
}
