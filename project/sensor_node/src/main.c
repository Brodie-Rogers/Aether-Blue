/**
************************************************************
* @file     project/mobile/src/main.c
* @author   Brodie Rogers - 45299823 and Riley Norris 44781796
* @date     17/05/2021
* @brief    Main file for project sensor node
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
#include <math.h>


#define ID_1 0xab
#define ID_2 0xc1 
#define NODE_NUM 2 //Change this for each node


//LED Device defines
#define LED0_NODE 	DT_ALIAS(led0)
#define LED0		DT_GPIO_LABEL(LED0_NODE, gpios)
#define PIN			DT_GPIO_PIN(LED0_NODE, gpios)
#define FLAGS		DT_GPIO_FLAGS(LED0_NODE, gpios)

#define LED1_NODE 	DT_ALIAS(led1)
#define LED1		DT_GPIO_LABEL(LED1_NODE, gpios)
#define PIN_BLUE	DT_GPIO_PIN(LED1_NODE, gpios)
#define FLAGS1		DT_GPIO_FLAGS(LED1_NODE, gpios)

#define LED2_NODE 	DT_ALIAS(led2)
#define LED2		DT_GPIO_LABEL(LED2_NODE, gpios)
#define PIN_RED		DT_GPIO_PIN(LED2_NODE, gpios)
#define FLAGS2		DT_GPIO_FLAGS(LED2_NODE, gpios)

//Other defines
#define RED 0
#define GREEN 1
#define BASELINE 48820

//Advertising data to represent node
static uint8_t data[] = {ID_2 , NODE_NUM, 0x12, 0x12, 0x12, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};


//Function prototypes
void reset_threshold(void);
void blink_led(void);
void read_temp_hum(void);
void get_hts_vals(void);

//Globals
int led_on = 0;
int led_sleep = 1000;
int current_led = GREEN;

static const struct bt_data ad[] = {
	BT_DATA(ID_1, data, 13),
};


const struct device *dev;
const struct device *hts_dev;
const struct device *led;
const struct device *blue_led;
const struct device *red_led;
struct ccs811_configver_type cfgver;
int rc;



/**
 * Thread defines for extra threads of operation
 */
K_THREAD_DEFINE(threshold_thread_id, 1024, reset_threshold, NULL, NULL, NULL, 5, 0, 0);
K_THREAD_DEFINE(led_thread_id, 1024, blink_led, NULL, NULL, NULL, 6, 0, 0);
K_THREAD_DEFINE(hts_thread_id, 1024, read_temp_hum, NULL, NULL, NULL, 5, 0, 0);



/**
**Scan callback for when bt data recieved
**/
static void scan_cb(const bt_addr_le_t *addr, int8_t rssi, uint8_t adv_type,
		    struct net_buf_simple *buf)
{

	int ID = ((buf->data)[1]) << 8 | ((buf->data)[2]);
	int node = (buf->data)[3];

    if (ID == 0xabc1) {

        if (node == 0xFF) {

			if ((buf->data)[4] == 'o') {
				current_led = GREEN;

			} else if ((buf->data)[4] == 'f') {
				current_led = RED;
			}
        }
    }
}

/**
 * Read from hts221, get temperature and humidity
 */
void read_temp_hum(void) {

	k_msleep(1000);

	while(1) {
		k_msleep(1000);
		get_hts_vals();
	}
}


/**
 * Reset threshold value if necessary
 */
void reset_threshold(void) {

	k_msleep(5000);

	while(1) {
		k_msleep(200);
		//ccs811_baseline_update(dev, BASELINE);
	}
}


/**
 * Blink LED based on measured CO2 levels
 */
void blink_led(void){

	while(1){

		if (current_led == GREEN) {
			gpio_pin_set(red_led, PIN_RED, 0);
			gpio_pin_set(led, PIN, (int)led_on);
			led_on ^= 1;
			if (led_sleep <= 1){
				k_msleep(20);
			} else {
				k_msleep(led_sleep);
			}
		}else if (current_led == RED) {
			gpio_pin_set(led, PIN, 0);
			gpio_pin_set(red_led, PIN_RED, (int)led_on);
			led_on ^= 1;
			if (led_sleep <= 1){
				k_msleep(20);
			} else {
				k_msleep(led_sleep);
			}
		}
	}
}


/**
 * Setup ccs811 air quality sensor
 */
void setup_ccs811(void) {

	dev = device_get_binding(DT_LABEL(DT_INST(0, ams_ccs811)));
}


/**
 * Setup hts221 temp and humidity sensor
 */
void setup_hts221(void){

	hts_dev = device_get_binding("HTS221");
}


/**
 * Get termp and humidity sensor readings
 */
void get_hts_vals(void){

	struct sensor_value temp;
	struct sensor_value hum;

	rc = sensor_sample_fetch(hts_dev);

	if (rc == 0) {

		sensor_channel_get(hts_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
		sensor_channel_get(hts_dev, SENSOR_CHAN_HUMIDITY, &hum);
	}

	data[8] = temp.val1;
	data[9] = temp.val2 / 10000;
	data[10] = hum.val1;
	data[11] = hum.val2 / 10000;

}


/**
 * Call get sensor channels
 */
static int get_sensor_vals(const struct device *dev)
{
	struct sensor_value co2; //, tvoc, voltage, current;
	struct sensor_value tvoc;


	int rc = 0;
	int baseline = -1;

	
	rc = sensor_sample_fetch(dev);

	if (rc == 0) {
		const struct ccs811_result_type *rp = ccs811_result(dev);
		sensor_channel_get(dev, SENSOR_CHAN_CO2, &co2);
		data[2] = (co2.val1 >> 8) & 0xFF;
		data[3] = (co2.val1) & 0xFF;
		led_sleep = 1000/((co2.val1*co2.val1)/160000) * 2;

		sensor_channel_get(dev, SENSOR_CHAN_VOC, &tvoc);
		data[4] = (tvoc.val1 >> 8) & 0xFF;
		data[5] = (tvoc.val1) & 0xFF;
	}
	
	return rc;
}


/**
 * Get baseline register values
 */
void get_baseline(void) {

	int baseline = ccs811_baseline_fetch(dev);

	data[6] = (baseline >> 8) & 0xFF;
	data[7] = baseline & 0xFF;
}


/**
 * Main function
 */
void main(void) {



	int ret;
	setup_ccs811();
	setup_hts221();

	led = device_get_binding(LED0);
	blue_led = device_get_binding(LED1);
	red_led = device_get_binding(LED2);
	ret = gpio_pin_configure(led, PIN, GPIO_OUTPUT_ACTIVE | FLAGS);
	ret = gpio_pin_configure(blue_led, PIN_BLUE, GPIO_OUTPUT_INACTIVE | FLAGS1);
	ret = gpio_pin_configure(red_led, PIN_RED, GPIO_OUTPUT_INACTIVE | FLAGS2);

	struct bt_le_scan_param scan_param = {
		.type       = BT_HCI_LE_SCAN_PASSIVE,
		.options    = BT_LE_SCAN_OPT_NONE,
		.interval   = 0x0010,
		.window     = 0x0010,
	};

	int err;
	err = bt_enable(NULL);

	ccs811_baseline_update(dev, BASELINE);
	err = bt_le_scan_start(&scan_param, scan_cb);
	

	while (1) {

		get_sensor_vals(dev);
		get_baseline();
		k_msleep(10);
		err = bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad),
				      NULL, 0);
		k_msleep(300);
		err = bt_le_adv_stop();

	} 
}
