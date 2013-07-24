# -*- coding: utf-8 -*-
# Uses python-usb (pyUSB) 1.0, not version 0.4 that comes with ubuntu by default.
# You may need to install python-pymongo and python-dateutil (and MongoDB) as well.

import sys
import usb.core
import usb.util
from pymongo import MongoClient
from datetime import datetime
from dateutil import tz
import time

#dev = usb.core.find(idVendor=0x3eb, idProduct=0x2022) # original fw
dev = usb.core.find(idVendor=0x1c40, idProduct=0x4d9) # generichid
interface = 0

assert dev is not None

if dev.is_kernel_driver_active(interface) is True:
  print "We need to detach kernel driver"
  dev.detach_kernel_driver(interface)

dev.set_configuration()
cfg = dev.get_active_configuration()

interface_number = cfg[(interface,0)].bInterfaceNumber
alternate_setting = 0#usb.control.get_interface(dev,interface_number)
intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number, bAlternateSetting = alternate_setting)

ep = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

assert ep is not None

#joypos = ['-', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', '?']
#but = ['-', '*']
temps=[300, 214.3, 178.2, 159.4, 147, 137.7, 130.5, 124.5, 119.5, 115.1, 111.3, 107.8, 104.7, 101.9, 99.4, 97, 94.8, 92.7, 90.8, 89, 87.3,
85.7, 84.2, 82.7, 81.3, 80, 78.7, 77.5, 76.3, 75.2, 74.1, 73.1, 72, 71, 70.1, 69.2, 68.3, 67.4, 66.5, 65.7, 64.9, 64.1, 63.4, 62.6,
61.9, 61.2, 60.5, 59.8, 59.1, 58.4, 57.8, 57.2, 56.5, 55.9, 55.3, 54.7, 54.2, 53.6, 53, 52.5, 51.9, 51.4, 50.9, 50.3, 49.8, 49.3,
48.8, 48.3, 47.8, 47.3, 46.9, 46.4, 45.9, 45.5, 45, 44.6, 44.1, 43.7, 43.2, 42.8, 42.4, 42, 41.5, 41.1, 40.7, 40.3, 39.9, 39.5,
39.1, 38.7, 38.3, 37.9, 37.5, 37.2, 36.8, 36.4, 36, 35.6, 35.3, 34.9, 34.5, 34.2, 33.8, 33.5, 33.1, 32.7, 32.4, 32, 31.7, 31.3, 31,
30.6, 30.3, 30, 29.6, 29.3, 28.9, 28.6, 28.3, 27.9, 27.6, 27.3, 26.9, 26.6, 26.3, 25.9, 25.6, 25.3, 25, 24.6, 24.3, 24, 23.6, 23.3,
23, 22.7, 22.4, 22, 21.7, 21.4, 21.1, 20.8, 20.4, 20.1, 19.8, 19.5, 19.1, 18.8, 18.5, 18.2, 17.9, 17.5, 17.2, 16.9, 16.6, 16.3,
15.9, 15.6, 15.3, 15, 14.6, 14.3, 14, 13.7, 13.3, 13, 12.7, 12.4, 12, 11.7, 11.4, 11, 10.7, 10.4, 10, 9.7, 9.3, 9, 8.7, 8.3, 8,
7.6, 7.3, 6.9, 6.6, 6.2, 5.8, 5.5, 5.1, 4.7, 4.4, 4, 3.6, 3.3, 2.9, 2.5, 2.1, 1.7, 1.3, 0.9, 0.5, 0.1, -0.3, -0.7, -1.1, -1.5, -2,
-2.4, -2.8, -3.3, -3.7, -4.2, -4.6, -5.1, -5.6, -6.1, -6.6, -7.1, -7.6, -8.1, -8.6, -9.1, -9.7, -10.3, -10.8, -11.4, -12,
-12.6,-13.3, -13.9, -14.6, -15.2, -15.9, -16.7, -17.4, -18.2, -19, -19.9, -20.7, -21.6, -22.6, -23.6, -24.7, -25.8, -27, -28.3,
-29.7, -31.2, -32.9, -34.7, -36.8, -39.2, -42.1, -45.7, -50.6, -58.4]

db = MongoClient().temperature
t0 = None
err_delay = 1

while 1:
  try:
    t = datetime.utcnow().replace(tzinfo=tz.tzutc())
    if t0 is not None:
      delta = (t - t0).total_seconds()
      if delta < 120:
        time.sleep(120 - delta)
        continue
    data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize*2, interface_number, 1000)
    data = data.tolist()
    #joy = data[3] % 16
    #if joy > 9: joy = 9
    #joybut = 1 if data[3] & 16 else 0
    #hwb = 1 if data[3] & 32 else 0
    adc = data[1]
    # occasionally fails silently, returning 0. Unlikely that temp is actually 300 °C so retry.
    if adc == 0: continue
    # table seems to be about 3 °C off, this makes it closer to actual temp (at least around mid 20s).
    temp = temps[adc] - 3.0
    print "%s: %d (%g °C)" % (t.astimezone(tz.tzlocal()), adc, temp)
    db.log.insert({'timestamp': t, 'adc': adc})
    t0 = t
    err_delay = 1
  except usb.core.USBError as e:
    print "Err:", e
    time.sleep(err_delay)
    if err_delay < 300:
      err_delay *= 2
