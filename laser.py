###############################################################
#                                                             #
# LASER: Lightweight And SEcure Remote keyless entry protocol #
#                                                             #
# Authors:                                                    #
# Vanesa Daza - vanesa.daza@upf.edu                           #
# Xavier Salleras - xavier.salleras@upf.edu                   #
#                                                             #
###############################################################

import sys
from rflib import *

from pyblake2 import blake2b
from threading import Thread
import keyboard 
import datetime

BANNER = "\n########## LASER v0.1 ##########"
OPERATING_FREQUENCIES = [432200000, 432500000, 432800000, 433100000] #MHz
MESSAGE_START = "LSRS"
MESSAGE_END = "LSRE"
ESTIMATED_VALUE_RKE = 0.085 #seconds
ESTIMATED_VALUE_PRKE = 0.17 #seconds

def set_rf():
    global test_env
    global endpoint_type
    
    if (test_env and endpoint_type == "fob"): endpoint = RfCat(idx=1)
    else: endpoint = RfCat(idx=0)
    
    endpoint.setModeRX()
    endpoint.setMdmModulation(MOD_ASK_OOK)
        
    return endpoint

def frequency_hopping(endpoint):
    global secret_key
    global frequency
    
    h = blake2b(digest_size=3)
    t_p = str(round(time.time(), -1))
    h.update(bytes(secret_key + t_p))
    h = h.hexdigest()
    
    index = int(h, 16) % len(OPERATING_FREQUENCIES)
    if (OPERATING_FREQUENCIES[index] != frequency):
        frequency = OPERATING_FREQUENCIES[index]
        endpoint.setFreq(frequency)
    
    return endpoint, h

def device_endpoint():
    global device_id
    global secret_key
    global exit
    global save_to_db
    
    device = set_rf()
    
    if (prke):
        print "\nPress 1 or 2 to do an action.\n"   
        while True:
            try:
                if keyboard.is_pressed('1'): device_request_auth(device, "01")
                if keyboard.is_pressed('2'): device_request_auth(device, "02")
            except:
                break           
    else:
        while not exit:
            device, h = frequency_hopping(device)
            laser_message = rx_laser_message(device)               
            if (laser_message):  
                t_end = time.time()           
                if (laser_message.device_id == device_id):        
                    h = blake2b(digest_size=3)
                    h.update(bytes(secret_key + laser_message.t_start))
                    t_e = t_end - float(laser_message.t_start)
                
                    if (laser_message.hash == h.hexdigest() and t_e < ESTIMATED_VALUE_RKE):
                        if (exchanging_times): 
                            print t_e
                        else:
                            ### Put here whatever you want to execute #########
                            print "COMMAND " + laser_message.cmd + " EXECUTED!"
                            ###################################################
                            log_protocol("Rx hash: " + laser_message.hash + " Exch. time: " + '{0:f}'.format(t_e))          
                        

def device_request_auth(device, command):
    global exchanging_times
       
    laser_message = LaserMessage(device_id)
    device, h = frequency_hopping(device)          
    device.RFxmit(laser_message.format())
    t_start = time.time()
    laser_message = rx_laser_message(device)  
     
    if (laser_message):
        t_end = time.time()
        t_e = t_end - t_start 
        if (laser_message.device_id == device_id):
            if (laser_message.hash == h and t_e < ESTIMATED_VALUE_PRKE): 
                if (exchanging_times): 
                    print '{0:f}'.format(t_e)
                else: 
                    ### Put here whatever you want to execute ###
                    print "COMMAND " + command + " EXECUTED!"
                    #############################################
                    log_protocol("Rx hash: " + laser_message.hash + " Exch. time: " + '{0:f}'.format(t_e))

def fob_endpoint():
    fob = set_rf()   
    if (prke):
        global device_id
        global secret_key
        while not exit:
            fob, h = frequency_hopping(fob)
            laser_message = rx_laser_message(fob)        
            if (laser_message):  
                if (laser_message.device_id == device_id): 
                    laser_message = LaserMessage(device_id, h)
                    fob.RFxmit(laser_message.format())
                    log_protocol("Tx hash: " + laser_message.hash)                        
    else:
        print "\nPress 1 or 2 to execute a command.\n"   
        while True:
            try:
                if keyboard.is_pressed('1'): fob_tx_cmd(fob, "01")
                if keyboard.is_pressed('2'): fob_tx_cmd(fob, "02")
            except:
                break           

def fob_tx_cmd(fob, command):
    global secret_key
    global device_id
    
    fob, h = frequency_hopping(fob)
    h = blake2b(digest_size=3)
    t_start = '{0:f}'.format(time.time())
    h.update(bytes(secret_key + t_start))
    laser_message = LaserMessage(device_id, h.hexdigest(), command, t_start)
    fob.RFxmit(laser_message.format())
    log_protocol("Tx hash: " + laser_message.hash) 

def rx_laser_message(device):
    global prke
    try:
        raw_message, timestamp = device.RFrecv(timeout=5000)

        laser_message = LaserMessage()
    
        i_start = raw_message.find(MESSAGE_START)
        i_end = raw_message.find(MESSAGE_END)
        if (i_start == -1 or i_end == -1): return None

        laser_message.start = raw_message[i_start : i_start + 4]
        laser_message.device_id = raw_message[i_start + 4 : i_start + 8]
        laser_message.hash = raw_message[i_start + 8 : i_start + 14]
        if not prke:
            laser_message.cmd = raw_message[i_start + 14 : i_start + 16]
            laser_message.t_start = raw_message[i_start + 16 : i_end]
        laser_message.end = raw_message[i_end : i_end + 4] 
    
        return laser_message
    except ChipconUsbTimeoutException:
        return None       

class LaserMessage():
    def __init__(self, device_id = "0000", hash_proof = "000000", cmd = "", t_start = ""):
        global prke
        self.start = MESSAGE_START
        self.device_id = device_id
        self.hash = hash_proof
        if not prke:
            self.cmd = cmd
            self.t_start = t_start
        self.end = MESSAGE_END   
        
    def format(self):
        global prke
        if (prke): return self.start + self.device_id + self.hash + self.end
        else: return self.start + self.device_id + self.hash + self.cmd + self.t_start + self.end
       
def log_protocol(log_text):
    global verbose
    if (verbose):
        print "[" + str(datetime.datetime.now()) + "] " + log_text

if len(sys.argv) < 3:
    print BANNER
    print "USAGE: sudo python laser.py [endpoint] [device_id] [secret_key] [OPTIONS]\n"
    print "endpoint: 'device' or 'fob'"
    print "device_id: 4 characters ID for the device"
    print "secret_key: non-fixed length preshared secret key\n"
    print "OPTIONS:"
    print "-p : Execute PRKE version."
    print "-t : Execute for testing purposes using two YS1 plugged in the same computer."
    print "-e : Print only exchanging times."
    print "-v : Verbose.\n"

else:
    frequency = 0
    exit = False
    test_env = False
    verbose = False
    endpoint_type = ""
    device_id = sys.argv[2]
    secret_key = sys.argv[3]
    prke = False
    exchanging_times = False
        
    if ("-t" in sys.argv): test_env = True
    if ("-v" in sys.argv): verbose = True
    if ("-p" in sys.argv): prke = True
    if ("-e" in sys.argv): exchanging_times = True
         
    if sys.argv[1] == "device":
        endpoint_type = "device"
        print BANNER
        print "LASER has started for a device."
        
        thread = Thread(target=device_endpoint, args=())
        thread.start()
        
        try:
            while True: pass
        except KeyboardInterrupt:
            exit = True

    if sys.argv[1] == "fob":
        endpoint_type = "fob"
        print BANNER
        print "LASER has started for a fob."
        fob_endpoint()