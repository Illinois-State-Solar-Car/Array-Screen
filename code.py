'''
Last Edit: 07/01/2025
Updated CAN addresses for multiple offset trackers

07/03/2024 Edits:
Made the total array wattage look a little nicer
Added comments


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
import fourwire
from adafruit_progressbar.verticalprogressbar import VerticalProgressBar, VerticalFillDirection
from adafruit_progressbar.progressbar import HorizontalProgressBar
from adafruit_display_shapes.arc import Arc




# Release the displays and start the clock


boot_time = time.monotonic()
displayio.release_displays()

# Create the SPI Buss
spi = busio.SPI(board.GP2, board.GP3, board.GP4)

#Create UART bus
uart = busio.UART(board.GP0,board.GP1,baudrate=9600)

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

display_bus = fourwire.FourWire(spi, command=dc, chip_select=cs, reset=reset, baudrate=1000000)
display = adafruit_ssd1325.SSD1325(display_bus, width=WIDTH, height=HEIGHT, rotation=180)
display.brightness = 1.0


startTime = time.time()
# Make the display context
splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(display.width, display.height, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Black

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a label
text = "    SOLAR CAR ISU\n     Array Screen\n\nYou Just Got Dunham'd"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_width = text_area.bounding_box[2] * FONTSCALE
text_group = displayio.Group(
    scale=FONTSCALE,
    x=display.width // 2 - text_width // 2,
    y=int(display.height / 6)
)
text_group.append(text_area)  # Subgroup for text scaling
splash.append(text_group)
time.sleep(2.5)
splash.pop(-1)


#initalizing our GUI elements.

totalWattage = HorizontalProgressBar(
    position=(0, 2),#position
    size=(128, 20),#size I'm maing absurdly big so that the jump from 50 to 70 fills more
    bar_color=0xFFFFFF,
    outline_color = 0xFFFFFF,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 1700
)

subarray1 = VerticalProgressBar(
    (0, 32),#position
    (16, 32),#size
    bar_color=0xFFFFFF,
    outline_color = 0xFFFFFF,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 600
)

subarray2 = VerticalProgressBar(
    (32, 32),#position
    (16, 32),#size
    bar_color=0xFFFFFF,
    outline_color = 0xFFFFFF,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 600
)

subarray3 = VerticalProgressBar(
    (64, 32),#position
    (16, 32),#size
    bar_color=0xFFFFFF,
    outline_color = 0xFFFFFF,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 600
)

subarray4 = VerticalProgressBar(
    (96, 32),#position
    (16, 32),#size
    bar_color=0xFFFFFF,
    outline_color = 0xFFFFFF,
    fill_color = 0x000000,
    border_thickness = 2,
    margin_size = 0,
    value = 0,
    min_value = 0,
    max_value = 600
)

MainWattageLabel = displayio.Group(scale=1, x=8, y=11)
wattage = label.Label(terminalio.FONT, text="0", color=0x000000)

SubArray1Label = displayio.Group(scale=1, x=0, y=28)
subarray1Label = label.Label(terminalio.FONT, text="1", color=0xFFFFFF)

SubArray2Label = displayio.Group(scale=1, x=32, y=28)
subarray2Label = label.Label(terminalio.FONT, text="2", color=0xFFFFFF)

SubArray3Label = displayio.Group(scale=1, x=64, y=28)
subarray3Label = label.Label(terminalio.FONT, text="3", color=0xFFFFFF)

SubArray4Label = displayio.Group(scale=1, x=96, y=28)
subarray4Label = label.Label(terminalio.FONT, text="4", color=0xFFFFFF)


MainWattageLabel.append(wattage)

SubArray1Label.append(subarray1Label)  # Subgroup for text scaling
SubArray2Label.append(subarray2Label)
SubArray3Label.append(subarray3Label)
SubArray4Label.append(subarray4Label)

def frontcover():
    #Draw Frontfilm over our text
    bitmap = displayio.OnDiskBitmap("resources/ArrayBitmap.bmp")
    bitmap.pixel_shader.make_transparent(0)
    frontfilm = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
    splash.append(frontfilm)
    
#helper function
def clamp(value, min, max):
    if value > max:
        return max
    if value < min:
        return min
    return value


#variable initialization
class Tracker():
    '''
    Elmar Solar Race MPPTs
    https://docs.prohelion.com/MPPTs/pdfs/Elmar%20Solar%20MPPT%20Race%202021.pdf
    '''
    def __init__(self):
        self.v_in = -1.0
        self.i_in = -1.0
        self.v_out = -1.0
        self.i_out = -1.0
        self.w = 0
        self.fet_temp = -1.0
        self.control_temp = -1.0

    def process600(self, data):
        '''
        Field, Message Bytes, Data Type, Units
        Input Voltage, 0-3, Float, Volt
        Input Current, 4-7, Float, Ampere
        '''
        holder = struct.unpack('<ff', next_message.data)
        self.v_in = holder[0]
        self.i_in = holder[1]

    def process601(self, data):
        '''
        Field, Message Bytes, Data Type, Units
        Output Voltage, 0-3, Float, Volt
        Output Current, 4-7, Float, Ampere
        '''
        holder = struct.unpack('<ff', next_message.data)
        self.v_out = holder[0]
        self.i_out = holder[1]
        self.w = self.v_out * self.i_out

    def process602(self, data):
        '''
        Field, Message Bytes, Data Type, Units
        Mosfet Temperature, 0-3, Float, Celcius
        Controller Temperature, 4-7, Float, Celcius
        '''
        holder = struct.unpack('<ff', next_message.data)
        self.fet_temp = holder[0]
        self.controller_temp = holder[1]
        
    def process603(self, data):
        '''
        Field, Message Bytes, Data Type, Units
        TBD
        TBD
        '''
        holder = struct.unpack('<ff', next_message.data)
        #TBD
        #TBD

tracker1 = Tracker()
tracker2 = Tracker()
tracker3 = Tracker()
tracker4 = Tracker()#TBD

totalWatt = send_time = 0


# two different functions for initialization of the screen and updating 
def initScreen():
    
    splash.append(subarray1)
    splash.append(subarray2)
    splash.append(subarray3)
    splash.append(subarray4)
    splash.append(totalWattage)
    
    splash.append(MainWattageLabel)
    
    splash.append(SubArray1Label)
    splash.append(SubArray2Label)
    splash.append(SubArray3Label)
    splash.append(SubArray4Label)
    
    frontcover()
    
    
    #Old Code below Return
    return
    # Draw labels for each of the arrays
    text_group = displayio.Group(scale=1, x=2, y=8)
    text = "   1      2      3"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    
    #write in the data coming from the subarrays
    text_group = displayio.Group(scale=1, x=2, y=20)
    text = "W:{:04.1f}   {:04.1f}   {:04.1f}".format(tracker1.w, tracker2.w, tracker3.w)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)
    
    #write in the total wattage we are getting from the array
    text_group = displayio.Group(scale=2, x=2, y=40)
    text = "  T:{:04.1f}".format(tracker1.w + tracker2.w + tracker3.w)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

    #display the temperatures we are getting from the power trackers
    text_group = displayio.Group(scale=1, x=2, y=60)
    text = "C:{:3.0f}    {:3.0f}    {:3.0f}".format(tracker1.fet_temp, tracker2.fet_temp, tracker3.fet_temp)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)


def drawScreen():
    
    #test values
    subarray1Value = tracker1.w
    subarray2Value = tracker2.w
    subarray3Value = tracker3.w
    subarray4Value = tracker4.w
    
    wattageValue = totalWatt
    
    
    subarray1RenderedValue = clamp(subarray1Value, 0, 600)
    subarray2RenderedValue = clamp(subarray2Value, 0, 600)
    subarray3RenderedValue = clamp(subarray3Value, 0, 600)
    subarray4RenderedValue = clamp(subarray4Value, 0, 600)
    
    TotalWattageRenderedValue = clamp(wattageValue, 0, 1700)
    
    subarray1.value = subarray1RenderedValue
    subarray2.value = subarray2RenderedValue
    subarray3.value = subarray3RenderedValue
    subarray4.value = subarray4RenderedValue
    
    totalWattage.value = TotalWattageRenderedValue
    wattage.text=str(TotalWattageRenderedValue) + " W"
    
    #now were gonna get a little fancy and try to make label be in center of filled bar.
    
    if TotalWattageRenderedValue < 400:
        MainWattageLabel.x = 48
        wattage.color = 0xFFFFFF
    else:
        wattage.color = 0x000000
        BarLocation = TotalWattageRenderedValue / (1700/128)
        
        #1700/128 to map value to screen width
        
        LabelMidpoint = BarLocation/2
        
        LabelLocation = LabelMidpoint - 16
        
        MainWattageLabel.x = int(LabelLocation)
    
    
    
    
    
    
    
    
    #Old Code Below Return
    return

    #write in the data coming from the subarrays
    text_group = displayio.Group(scale=1, x=2, y=20)
    text = "W:{:04.1f}   {:04.1f}   {:04.1f}".format(tracker1.w, tracker2.w, tracker3.w)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-3] = text_group
    
    #write in the total wattage we are getting from the array
    text_group = displayio.Group(scale=2, x=2, y=40)
    text = "  T:{:04.1f}".format(tracker1.w + tracker2.w + tracker3.w)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-2] = text_group

    #display the temperatures we are getting from the power trackers
    text_group = displayio.Group(scale=1, x=2, y=60)
    text = "C:{:3.0f}    {:3.0f}    {:3.0f}".format(tracker1.fet_temp, tracker2.fet_temp, tracker3.fet_temp)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_group.append(text_area)  # Subgroup for text scaling
    splash[-1] = text_group
    

def _shaune_theCAN_isfull():
    message_count = listener.in_waiting()
    if message_count >300:
        mcp._unread_message_queue.clear()


initScreen() #initialize the screens
time.sleep(0.2)

runTime = time.time()

while True:
    #get the CAN data
    with mcp.listen(timeout=0) as listener:
        #send data to portenta through the uart line
        current_time = time.time()
        time_since_send = send_time - current_time
        if time_since_send > 1:
            # TODO: I don't know what the protocol is here to throw a 3rd temp in
            uart.write(struct.pack('<ffffff', tracker1.w, tracker2.w, tracker3.w, totalWatt, tracker1.fet_temp, tracker2.fet_temp))
            send_time=time.time()

        totalWatt = tracker1.w + tracker2.w + tracker3.w #calculate total wattage

        _shaune_theCAN_isfull()
        
        drawScreen() #update the screen with CAN data
        #Here starts where we do the CAN things
        message_count = listener.in_waiting()
        print("message count = {}".format(message_count), end = '\n')
        if message_count == 0:
            continue
        next_message = listener.receive()
        
        #TODO: Add a lines here for the new tracker
        while next_message is not None:
            # Check the id to properly unpack it
            if next_message.id == 0x610:
                tracker1.process600(next_message.data)
            elif next_message.id == 0x611:
                tracker1.process601(next_message.data)
            elif next_message.id == 0x612:
                tracker1.process602(next_message.data)
            elif next_message.id == 0x620:
                tracker2.process600(next_message.data)
            elif next_message.id == 0x621:
                tracker2.process601(next_message.data)
            elif next_message.id == 0x622:
                tracker2.process602(next_message.data)
            elif next_message.id == 0x630:
                tracker3.process600(next_message.data)
            elif next_message.id == 0x631:
                tracker3.process601(next_message.data)
            elif next_message.id == 0x632:
                tracker3.process602(next_message.data)
            next_message = listener.receive()            

