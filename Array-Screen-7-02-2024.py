'''
Last Edit: 07/02/2024

Patch Notes:
updated to show the full array wattage
made the subarray wattage displays smaller to make space for the full array wattage


The Following code is for the array driver display

Please make sure to include the following in the lib folder:
adafruit_display_text
adafruit_mcp2515
adafruit_ssd1325.py
'''

import board
import busio
import math
import struct
import time
import analogio
import digitalio
import displayio
import terminalio
import adafruit_ssd1325
from adafruit_mcp2515       import MCP2515 as CAN
from adafruit_mcp2515.canio import RemoteTransmissionRequest, Message, Match, Timer
from adafruit_display_text import label
import adafruit_mcp2515
import microcontroller 


"""
======================================================================================================================================
MPPT CANBus Codes
-----------------
Message ID | Value 1            | Value 2            | Value 3         | Value 4     |
--------------------------------------------------------------------------------------
0x600      | Subarray 1 Voltage | Subarray 1 Current | Battery Voltage | MPPT 1 Temp |
0x601      | Subarray 2 Voltage | Subarray 2 Current | Battery Voltage | MPPT 1 Temp |
0x602      | Subarray 3 Voltage | Subarray 3 Current | Battery Voltage | MPPT 2 Temp |
======================================================================================================================================
"""

# Release the displays and start the clock
boot_time = time.monotonic()
displayio.release_displays()

# Create the SPI Buss
spi = busio.SPI(board.GP2, board.GP3, board.GP4)

#Create UART bus
#uart = busio.UART(board.GP0,board.GP1,baudrate=9600)

# Set up the MCP 2515 on the SPI Bus
can_cs = digitalio.DigitalInOut(board.GP9)
can_cs.switch_to_output()
mcp = CAN(spi, can_cs, baudrate = 500000, crystal_freq = 16000000, silent = False,loopback = False)

# Set up the OLED on the SPI Bus
cs = board.GP20
dc = board.GP10
reset = board.GP19
WIDTH = 128
HEIGHT = 64
BORDER = 0
FONTSCALE = 1

display_bus = displayio.FourWire(spi, command=dc, chip_select=cs, reset=reset, baudrate=1000000)
display = adafruit_ssd1325.SSD1325(display_bus, width=WIDTH, height=HEIGHT)
display.brightness = 1.0



startTime = time.time()
# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(display.width, display.height, 1)
color_palette = displayio.Palette(1)
color_palette[0] =0x000000  # Black

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a label
text = "SOLAR CAR ISU ARRAY"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_width = text_area.bounding_box[2] * FONTSCALE
text_group = displayio.Group(
    scale=FONTSCALE,
    x=display.width // 2 - text_width // 2,
    y=display.height // 2,
)
text_group.append(text_area)  # Subgroup for text scaling
splash.append(text_group)
time.sleep(2.5)
splash.pop(-1)




subArr1V = subArr1I = subArr2V = subArr2I = subArr3V = subArr3I = mppttemp1 = mppttemp2 = -1

subArr1W = subArr2W = subArr3W = totalWatt = sendtime = 0





def initScreen():
    # Draw Speed/effecency Label
    text_group = displayio.Group(scale=1, x=2, y=8)
    text = "Arr1: {:04.1f}".format(subArr1W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    # Draw Effecency Label
    text_group = displayio.Group(scale=1, x=2, y=20)
    text = "Arr2: {:04.1f}".format(subArr2W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    text_group = displayio.Group(scale=1, x=2, y=32)
    text = "Arr3: {:04.1f}".format(subArr3W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    
    text_group = displayio.Group(scale=2, x=2, y=44)
    text = "Total: {:04.1f}".format((subArr1W + subArr2W + subArr3W))
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    # Draw temp labels for MPPTs
    text_group = displayio.Group(scale=1, x=10, y=60)
    text = "T1: {:04.1f}  T2: {:04.1f}".format(mppttemp1,mppttemp2)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    
def drawScreen():
    text_group = displayio.Group(scale=1, x=2, y=8)
    text = "Arr1: {:04.1f}".format(subArr1W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-5] = text_group

    # Draw Effecency Label
    text_group = displayio.Group(scale=1, x=2, y=20)
    text = "Arr2: {:04.1f}".format(subArr2W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-4] = text_group

    text_group = displayio.Group(scale=1, x=2, y=32)
    text = "Arr3: {:04.1f}".format(subArr3W)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-3] = text_group    text_group = displayio.Group(scale=2, x=2, y=46)
    
    text_group = displayio.Group(scale=2, x=2, y=44)
    text = "Total: {:04.1f}".format((subArr1W + subArr2W + subArr3W))
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-2] = text_group

    # Draw voltage/current Label
    text_group = displayio.Group(scale=1, x=10, y=60)
    text = "T1: {:04.1f}  T2: {:04.1f}".format(mppttemp1,mppttemp2)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-1] = text_group
    

def _shaune_theCAN_isfull():
    message_count = listener.in_waiting()
    if message_count >300:
        mcp._unread_message_queue.clear()


initScreen()
time.sleep(0.2)

runTime = time.time()

while True:
        
    with mcp.listen(timeout=0) as listener:
        '''
        if(time.time()-sendtime>1):
            uart.write(struct.pack('<ffffff',subArr1W,subArr2W,subArr3W,totalWatt,mppttemp1,mppttemp2))
            sendtime=time.time()

        totalWatt = subArr1W+subArr2W+subArr3W
        '''
        _shaune_theCAN_isfull()
        
        drawScreen()
        #Here starts where we do the CAN things
        message_count = listener.in_waiting()
        print("message count = {}".format(message_count),end = '\n')
        if message_count == 0:

            continue
        
        next_message = listener.receive()
        message_num = 0

        
        while not next_message is None:
        
            message_num += 1

            # Check the id to properly unpack it
            if next_message.id == 0x600:

            #unpack and print the message
                holder = struct.unpack('<hhhh',next_message.data)
                subArr1V = holder[0]
                subArr1I = holder[1]
                subArr1W = subArr1V*subArr1I
                
                #print("Message From: {}: [V = {}; A = {}]".format(hex(next_message.id),voltage,current))



            if next_message.id == 0x601:

            #unpack and print the message
                holder = struct.unpack('<hhhh',next_message.data)
                subArr2V = holder[0]
                subArr2I = holder[1]
                subArr2W = subArr2V*subArr2I
                mppttemp1 = holder[3]
                
                #print("Message From: {}: [V = {}; A = {}]".format(hex(next_message.id),voltage,current))


            if next_message.id == 0x602:

            #unpack and print the message
                holder = struct.unpack('<hhhh',next_message.data)
                subArr3V = holder[0]
                subArr3I = holder[1]
                subArr3W = subArr3V*subArr3I
                mppttemp2 = holder[3]
                
                #print("Message From: {}: [V = {}; A = {}]".format(hex(next_message.id),voltage,current))


            next_message = listener.receive()            



    


