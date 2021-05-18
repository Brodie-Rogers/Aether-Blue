/**
************************************************************
* @file     project/mobile/src/main.c
* @author   Brodie Rogers - 45299823 and Riley Norris 44781796
* @date     17/05/2021
* @brief    Main file for p3 mobile node
************************************************************
**/

#include <zephyr.h>
#include <zephyr/types.h>
#include <stddef.h>
#include <sys/util.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <drivers/sensor/ccs811.h>
#include <devicetree.h>
#include <drivers/gpio.h>
#include <device.h>
#include <stdio.h>


#define ID_1 0xab
#define ID_2 0xc1 
#define NODE_NUM 2 //Change this for each node

#define LED0_NODE DT_ALIAS(led0)
#define LED0	DT_GPIO_LABEL(LED0_NODE, gpios)
#define PIN	DT_GPIO_PIN(LED0_NODE, gpios)
#define FLAGS	DT_GPIO_FLAGS(LED0_NODE, gpios)


//Advertising data to represent node
static uint8_t data[] = {ID_2 , NODE_NUM, 0x12, 0x12, 0x12, 0x12};

static const struct bt_data ad[] = {
	BT_DATA(ID_1, data, 9),
};


const struct device *dev;
const struct device *led;
struct ccs811_configver_type cfgver;
int rc;



/**
**Scan callback for when bt data recieved
**/
// static void scan_cb(const bt_addr_le_t *addr, int8_t rssi, uint8_t adv_type,
// 		    struct net_buf_simple *buf)
// {

// 	int ID = ((buf->data)[1]) << 8 | ((buf->data)[2]);
// 	int node = 0;
// 	int ultrasonic = 0;

	
// }


void setup_ccs811(void) {

	dev = device_get_binding(DT_LABEL(DT_INST(0, ams_ccs811)));
}



static int get_sensor_vals(const struct device *dev)
{
	struct sensor_value co2; //, tvoc, voltage, current;
	struct sensor_value tvoc;
	int rc = 0;
	int baseline = -1;

	if (rc == 0) {
		rc = sensor_sample_fetch(dev);
	}
	if (rc == 0) {

		const struct ccs811_result_type *rp = ccs811_result(dev);

		sensor_channel_get(dev, SENSOR_CHAN_CO2, &co2);

		data[2] = (co2.val1 >> 8) & 0xFF;
		data[3] = (co2.val1) & 0xFF;
		sensor_channel_get(dev, SENSOR_CHAN_VOC, &tvoc);

		data[4] = (tvoc.val1 >> 8) & 0xFF;
		data[5] = (tvoc.val1) & 0xFF;

		//printk("\n[%s]: CCS811: %u ppm eCO2; %u ppb eTVOC\n",
		     //  now_str(), co2.val1, tvoc.val1);
		//printk("Voltage: %d.%06dV; Current: %d.%06dA\n", voltage.val1,
		       //voltage.val2, current.val1, current.val2);

	}
	return rc;
}


/**
 * Main function
 */
void main(void) {

	int ret;
	setup_ccs811();
	int led_on = 0;

	led = device_get_binding(LED0);
	ret = gpio_pin_configure(led, PIN, GPIO_OUTPUT_ACTIVE | FLAGS);

	struct bt_le_scan_param scan_param = {
		.type       = BT_HCI_LE_SCAN_PASSIVE,
		.options    = BT_LE_SCAN_OPT_NONE,
		.interval   = 0x0010,
		.window     = 0x0010,
	};

	int err;
	err = bt_enable(NULL);
	//err = bt_le_scan_start(&scan_param, scan_cb);

	while (1) {

		get_sensor_vals(dev);

		gpio_pin_set(led, PIN, (int)led_on);
		led_on ^= 1;

		k_msleep(100);

		err = bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad),
				      NULL, 0);

		k_msleep(100);

		err = bt_le_adv_stop();

	} 
}
