#!/usr/bin/python3
# version 0.3

import sys
import os
import time
import subprocess
import pickle
from distutils.util import strtobool


def Show_data(power, ffile, currTime_str):
    SCREEN_HEIGHT = 500
    TOP_POWER = 1200
    istant_power_info = f"""
    <h2 align=center>  Position: N45.1815 - E9.4793 <br> </h2>
    <h3 align=center> (San Colombano Lambro - Italy - 2 strings) <br> </h3> 

    <TABLE border="2" cellpadding="5" cellspacing="0" align=center>
    <TR>
    <TD align="middle" colspan=3">Power @{currTime_str}</TD>
    </TR>
    <TR Valign="bottom" align="center">
    
    <TD height="{SCREEN_HEIGHT}" width="25">
    <TABLE>
    <TR> <TD height="{SCREEN_HEIGHT / 2}" width="25" valign="top" align="right"> <small>{TOP_POWER}</small> </TD></TR>
    <TR> <TD height="{SCREEN_HEIGHT / 2}" valign="bottom" align="right"> <small>0</small> </TD></TR>
    </TABLE>
    </TD>
    
    <TD height="{SCREEN_HEIGHT}"><IMG src="pixel.jpg" width="100" height="{power[0] / TOP_POWER * SCREEN_HEIGHT}"></TD>
    <TD> <IMG src="pixel.jpg" width="100" height="{power[1] / TOP_POWER * SCREEN_HEIGHT}"></TD>
    </TR>
    
    <TR align="center">
    <TD></TD>
    <TD>{power[0]} Watt </TD>
    <TD>{power[1]} Watt</TD>
    </TR>
    <TR align="center">
    <TD></TD>
    <TD>azimut: 105 deg<br>height: 70 deg</TD><TD>azimut: 285 deg<br>height: 70 deg</TD>
    </TR>
    </TABLE>
    """
    ffile.write(istant_power_info)
    ffile.close()


def aurora_check(test):

    twilightTime=30

    currTime_raw=subprocess.check_output("date +%H:%M", shell=True)
    currTime_str=currTime_raw.decode('utf-8')
    currTime_trm=currTime_str[-7:-1]
    currTime=currTime_trm.split(':')
    # change time as int...
    for index, item in enumerate(currTime):
        currTime[index] = int(item)

    timeMin=currTime[0]*60+currTime[1]
    if test:
        print("current time:", currTime)
        print("current time (min):", timeMin, '\n')

    sunTime_raw=subprocess.check_output("hdate", shell=True)
    sunTime_raw_str=sunTime_raw.decode('utf-8')

    sunTime_sunrise=sunTime_raw_str[-12:-7]
    sunRise=sunTime_sunrise.split(':')
    for index, item in enumerate(sunRise):
        sunRise[index] = int(item)
    sunRiseMin=sunRise[0]*60+sunRise[1]

    sunTime_sunset=sunTime_raw_str[-6:-1]
    sunSet=sunTime_sunset.split(':')
    for index, item in enumerate(sunSet):
        sunSet[index] = int(item)
    sunSetMin=sunSet[0]*60+sunSet[1]

    if test:
        print("sunrise: ", sunRise)
        print("sunRise (min):", sunRiseMin, '\n')
        print("sunset: ", sunSet)
        print("sunSet (min):", sunSetMin, '\n')

    if ((timeMin > sunRiseMin) and (timeMin <= (sunSetMin+twilightTime)) or (test)):    # daytime... (or testing time)

        ffile = open(r'night.pkl', 'rb')
        night_flag = pickle.load(ffile)
        ffile.close()
        if night_flag=="night":    # first reading of the day....
                night_flag = "day"
                ffile = open(r'night.pkl', 'wb')
                pickle.dump(night_flag, ffile)
                ffile.close()
        # regular day reading ...
        if test:
            record_fakeR = """
                        printf 'Input 1 Power               =     99.999999 W\nInput 2 Power               =     99.999999 W' > curRead.tmp
                        """
            os.system(record_fakeR)
        else:
            readPower = './aurora -a2 -t -d0 -P100 -Y10 /dev/ttyUSB0 > curRead.tmp'
            os.system(readPower)
            time.sleep(2)

        extractData='grep "date\|1[[:blank:]]Power\|2[[:blank:]]Power" curRead.tmp >> aurora.log'
        os.system(extractData)

        power = [0, 0]
        get_power = 'grep "1[[:blank:]]Power" curRead.tmp'
        currPower_raw = subprocess.check_output(get_power, shell=True)
        currPower_str = currPower_raw.decode('utf-8')
        currPower_trm = currPower_str[-13:-3]
        power[0]=round(float(currPower_trm))    # string 1 power in power[0]

        get_power = 'grep "2[[:blank:]]Power" curRead.tmp'
        currPower_raw = subprocess.check_output(get_power, shell=True)
        currPower_str = currPower_raw.decode('utf-8')
        currPower_trm = currPower_str[-13:-3]
        power[1] = round(float(currPower_trm))  # string 2 power in power[0]

        if test:
            ffile = open('index.html', 'w')
        else:
            ffile = open('/var/www/html/index.html', 'w')

        Show_data(power, ffile, currTime_str)


    else:        # night
        ffile = open(r'night.pkl', 'rb')
        night_flag = pickle.load(ffile)
        ffile.close()
        if night_flag=="day":   # first night operation ...
                night_flag = "night"
                ffile = open(r'night.pkl', 'wb')
                pickle.dump(night_flag, ffile)
                ffile.close()

                printMarker='printf "night: no reading\n\n\n"  >> aurora.log'    # so record it
                os.system(printMarker)

                Show_data([0, 0])



if __name__ == "__main__":
    for arg in sys.argv[1:2]:
        aurora_check(strtobool(arg))
