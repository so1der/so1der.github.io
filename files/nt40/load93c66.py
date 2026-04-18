#!/usr/bin/python

#============================================================
# The original scripts for 93C56 can be found here:
# https://forums.raspberrypi.com/viewtopic.php?t=140764
#
# Write 93C66 with raspberry PI
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

import sys
import RPi.GPIO as GPIO
from bitarray import bitarray

# Create a delay for operations


def delay():
    a = 0
    for i in range(1000):
        a = a + 1


def sendCommand(command):
    # Set all pin to 0
    GPIO.output(CS, False)
    GPIO.output(CLK, False)
    GPIO.output(R_OUT, False)

    # Start condition
    GPIO.output(CS, True)
    delay()

    # issue bits
    for bitIndex in range(12):
        bit = (command >> (11 - bitIndex)) & 1
        GPIO.output(R_OUT, bit)
        delay()
        GPIO.output(CLK, True)
        delay()
        GPIO.output(CLK, False)
        GPIO.output(R_OUT, False)


# Pin mapping
GPIO.setmode(GPIO.BOARD)
CS = 31  # To eeprom CS
CLK = 33  # To eeprom CLK
R_OUT = 35  # To eeprom DI
R_IN = 37  # To eeprom DO

# Setup GPIO
GPIO.setup(CS, GPIO.OUT)  # CS  eeprom
GPIO.setup(CLK, GPIO.OUT)  # CLK eeprom
GPIO.setup(R_OUT, GPIO.OUT)  # DI  eeprom
GPIO.setup(R_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # DO  eeprom

# Define operation and base address
enable_write = 0b100110000000
disable_write = 0b100000000000
erase_all = 0b100100000000
start_write = 0b101000000000

# Load data
f = open("dump.bin", "rb")
binContent = bitarray(endian='big')
binContent.fromfile(f)
f.close()
if(len(binContent) != 4096):
    print("Error. The file length is invalid : {} bits".format(len(binContent)))
    exit()

print("Start loading dump.bin ")

#=====================================================
# Send Write enable operation (12 bit starting from MSB)
#=====================================================
sendCommand(enable_write)

# init position of bit in the file
bitFileIndex = 0

#==================
# Loop for 512 words
#==================
for wordIndex in range(512):
    # Set all pin to 0 before issueing start
    GPIO.output(CS, False)
    GPIO.output(CLK, False)
    GPIO.output(R_OUT, False)

    # Start condition
    GPIO.output(CS, True)
    delay()

    # Send Write operation and address (12 bit starting from MSB)
    for bitIndex in range(12):
        bit = ((start_write + wordIndex) >> (11 - bitIndex)) & 1
        GPIO.output(R_OUT, bit)
        delay()
        GPIO.output(CLK, True)
        delay()
        GPIO.output(CLK, False)
        GPIO.output(R_OUT, False)

    # Send 8 bits
    for index in range(8):
        GPIO.output(R_OUT, binContent[bitFileIndex])
        delay()
        GPIO.output(CLK, True)
        delay()
        GPIO.output(CLK, False)
        GPIO.output(R_OUT, False)
        # Move to next bit
        bitFileIndex += 1

    # Set CS to low and send CLK rising edge to start auto erase
    GPIO.output(CS, False)
    delay()
    GPIO.output(CS, True)
    GPIO.output(CLK, True)
    delay()
    GPIO.output(CLK, False)

    timeout = 1000    
    while (GPIO.input(R_IN) == 0):
        delay()
        timeout -= 1
        if(timeout == 0):
            print("Timeout error at word {}".format(wordIndex+1))
            GPIO.cleanup()
            exit()
    
    sys.stdout.write("\r" + str(wordIndex + 1))
    sys.stdout.flush()

print("\r\nFlashing done")

#======================================================
# Send Write disable operation (12 bit starting from MSB)
#==================================================\====
sendCommand(disable_write)

# Deactivate chip
GPIO.output(CLK, False)
GPIO.output(CS, False)

# Release GPIOS
GPIO.cleanup()
