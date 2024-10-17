import logging
import configparser
import os
import sys
import threading
import queue
from time import sleep
from renogybt import InverterClient, RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils
from renogybt.Models import DeviceModel

logging.basicConfig(level=logging.DEBUG)

config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
config = configparser.ConfigParser(inline_comment_prefixes=('#'))
config.read(config_path)
data_logger: DataLogger = DataLogger(config)

# Create battery and charge controller device models
battery_device = DeviceModel(
    adapter=config['battery']['adapter'],
    mac_addr=config['battery']['mac_addr'],
    alias=config['battery']['alias'],
    type=config['battery']['type'],
    device_id=int(config['battery']['device_id'])
)

charge_controller_device = DeviceModel(
    adapter=config['charge_controller']['adapter'],
    mac_addr=config['charge_controller']['mac_addr'],
    alias=config['charge_controller']['alias'],
    type=config['charge_controller']['type'],
    device_id=int(config['charge_controller']['device_id'])
)

# the callback func when you receive data
def on_data_received(client, data):
    filtered_data = Utils.filter_fields(data, config['data']['fields'])
    logging.debug("{} => {}".format(client.device.alias(), filtered_data))
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=filtered_data)
    if config['mqtt'].getboolean('enabled'):
        data_logger.log_mqtt(json_data=filtered_data)
    if config['pvoutput'].getboolean('enabled') and config['device']['type'] == 'RNG_CTRL':
        data_logger.log_pvoutput(json_data=filtered_data)
    if not config['data'].getboolean('enable_polling'):
        client.disconnect()

# error callback
def on_error(client, error):
    logging.error(f"on_error: {error}")

def battery_thread(config, battery_device, on_data_received, on_error):
    battery_client = BatteryClient(config, battery_device, on_data_received, on_error)
    battery_client.connect()

def controller_thread(config, charge_controller_device, on_data_received, on_error):
    rover_client = RoverClient(config, charge_controller_device, on_data_received, on_error)
    rover_client.connect()

# Start Battery thread
battery_thread = threading.Thread(target=battery_thread, args=(config, battery_device, on_data_received, on_error))
battery_thread.start()

sleep(10)

# Start Charge Controller thread
controller_thread = threading.Thread(target=controller_thread, args=(config, charge_controller_device, on_data_received, on_error))
controller_thread.start()



# Start Charge Controller Client
#rover_client = RoverClient(config, charge_controller_device, on_data_received, on_error)
#rover_client.connect()

'''
# start client
if config['device']['type'] == 'RNG_CTRL':
    RoverClient(config, on_data_received, on_error).connect()
elif config['device']['type'] == 'RNG_CTRL_HIST':
    RoverHistoryClient(config, on_data_received, on_error).connect()
elif config['device']['type'] == 'RNG_BATT':
    battery_client = BatteryClient(config, on_data_received, on_error)
    battery_client.connect()
elif config['device']['type'] == 'RNG_INVT':
    InverterClient(config, on_data_received, on_error).connect()
else:
    logging.error("unknown device type")
'''