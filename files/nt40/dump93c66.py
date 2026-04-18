#!/usr/bin/python

#============================================================
# The original scripts for 93C56 can be found here:
# https://forums.raspberrypi.com/viewtopic.php?t=140764
#
# Dump 93C66 with raspberry PI
#
# SPI is not usable for microwire eeprom (12 bits commmands).
# It's quite easy to do bit banging instead as microwire protocol is simple
# Note that the eeprom is supposed to work from 4.5V to 5.5v. In fact they
# work at 3.3v - DON'T connect VCC to 5V otherwise DO pin will issue 5V and
# ruin your PI.
#
# Connections (direct wire, dirty but works):
#               EEPROM VCC to PI 3.3v
#               EEPROM ORG to PI GND
#               EEPROM CS to pin 31
#               EEPROM CLK to pin 33
#               EEPROM DI to pin 35
#               EEPROM DO to pin 37
#
# Memory organization is set to 8 bit (connect ORG pin to GND)
#
# You need bitarray and RPI.GPIO libraries.
#
# Adjust the number of loops in delay() function. On a standard raspberry pi 2
# the CLK frequency is approx 6.5 KHZ for 100.
#============================================================

import RPi.GPIO as GPIO
from bitarray import bitarray
import time

# Create a delay for operations


def delay():
    a = 0
    for i in range(1000):
        a = a + 1

# open file in which to save eeprom dump
f = open("dump.bin", "wb")

# Pin mapping
GPIO.setmode(GPIO.BOARD)
CS = 31  # To eeprom CS
CLK = 33  # To eeprom CLK
R_OUT = 35  # To eeprom DI
R_IN = 37  # To eeprom DO

# Setup GPIO
GPIO.setup(CS, GPIO.OUT)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(R_OUT, GPIO.OUT)
GPIO.setup(R_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define operation and base address
start_read = 0b110000000000

# Set all pin to 0
GPIO.output(CS, False)
GPIO.output(CLK, False)
GPIO.output(R_OUT, False)

print("Start reading memory...")

# Start condition
GPIO.output(CS, True)
delay()

# Send read operation and address (12 bit starting from MSB)
for bitIndex in range(12):
    bit = (start_read >> (11 - bitIndex)) & 1
    GPIO.output(R_OUT, bit)
    delay()
    GPIO.output(CLK, True)
    delay()
    GPIO.output(CLK, False)
    GPIO.output(R_OUT, False)


# Read memory sequentially
binContent = bitarray(endian='big')
for bitIndex in range(4096):
    delay()
    GPIO.output(CLK, True)
    delay()
    binContent.append(GPIO.input(R_IN))
    GPIO.output(CLK, False)

# Deactivate chip
GPIO.output(CLK, False)
GPIO.output(CS, False)

# Write to file
binContent.tofile(f)

# Save file
f.close()

# Release GPIOS
GPIO.cleanup()

print ("{} bytes copied to dump.bin".format(len(binContent) / 8))
