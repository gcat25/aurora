#!/usr/bin/python3
#
# versione 0.4.2
# inserisco sistema di controllo del sw tra un avvio
# e il successivo attraverso una variabile di stato registrata
# su file. stati:
# "ACTIVE"
# "SLEEPING"
# nuova ripartizione del codice tra main e procedure
#
#
# versione 0.4.1
# miglioro schermate power e energia
#
#
# versione 0.4
# 1 aggiungo istogramma produzione
#
#
# version 0.3 - prima versione di produzione - changelog
# 0 aggiorna file di log e pagina web con istogramma produzione
# 1 opera come standalone, per il test, o come modulo
# 2 web page delegata a un metodo
#


import sys
import os
import time
import subprocess
import pickle
from distutils.util import strtobool

daily_data = []

def Show_data(power, ffile, currTime_str, daily_power):
    SCREEN_HEIGHT = 600
    TOP_POWER = 1200
    POWER_VIEW_WIDTH = 200
    PROD_VIEW_WIDTH = 400


    istant_power_info = f"""
    <h2 align=center>  Position: N45.1815 - E9.4793 <br> </h2>
    <h3 align=center> (San Colombano Lambro - Italy - 2 strings) <br> </h3>

    <TABLE border="2" cellpadding="2" cellspacing="0" align=center>
    <TR><TD align="middle" colspan=2">Power @{currTime_str}</TD></TR>
    <TR Valign="bottom" align="center">

    <TD height="{SCREEN_HEIGHT} valign="bottom" style="background-image: url('band.png');"><IMG src="pixelv.jpg" width="{POWER_VIEW_WIDTH}" height="{power[0] / TOP_POWER * SCREEN_HEIGHT}"></TD>
    <TD style="background-image: url('band.png');"> <IMG src="pixelb.jpg" width="{POWER_VIEW_WIDTH}" height="{power[1] / TOP_POWER * SCREEN_HEIGHT}"></TD>
    </TR>

    <TR align="center">
    <TD>{power[0]} Watt </TD>
    <TD>{power[1]} Watt</TD>
    </TR>
    <TR align="center">
    <TD>azimut: 105 deg<br>height: 70 deg</TD><TD>azimut: 285 deg<br>height: 70 deg</TD>
    </TR>
    <br>
    </TABLE>
    """
    ffile.write(istant_power_info)

    day_prod_info = f"""
    <h2 align=center>  Position: N45.1815 - E9.4793 <br> </h2>
    <h3 align=center> (San Colombano Lambro - Italy - 2 strings) <br> </h3>
    <h3 align=center> Daily production till {currTime_str}<br> </h3>

    <TABLE border="2" cellpadding="2" cellspacing="2" align=center>
    <TR Valign="bottom" align="center">
    <TD>
    <TABLE border="0" cellpadding="0" cellspacing="0" align=center>
    <TR style="background-image: url('band.png');" Valign="bottom" align="center">
    """
    day_prod_info_list = [day_prod_info]
    for element in daily_data:
        new_info = f"""
        <TD height={SCREEN_HEIGHT}><IMG src="pixelv.jpg" width={PROD_VIEW_WIDTH/(len(daily_data) + 4)} height= {element[1] / TOP_POWER * SCREEN_HEIGHT}></TD>
        """
        day_prod_info_list.append(new_info)
        new_info = f"""
        <TD height={SCREEN_HEIGHT}><IMG src="pixelb.jpg" width={PROD_VIEW_WIDTH / (len(daily_data) + 4)} height= {element[2] / TOP_POWER * SCREEN_HEIGHT}></TD>
        """
        day_prod_info_list.append(new_info)

    day_prod_info_list.append("</TR></TABLE>")
    day_prod_info = ''.join(day_prod_info_list)
    ffile.write(day_prod_info)
    ffile.close()


def actual_prod_data(test):

    first_reading = True
    current_data = "undefined"
    for line in reversed(open("aurora.log").readlines()):

        if (str(line).find("night") == -1 or str(line) == ""):  # do nothing for night and null recordings

            if (str(line).find("Input 1 Power") != -1):
                pw1 = float(str(line[30:44]))
            if (str(line).find("Input 2 Power") != -1):
                pw2 = float(str(line[30:44]))
            if (str(line).find("date/time") != -1):
                date = str(line[28:39])
                hour = str(line[40:45])
                if first_reading:  # record data for further control ...
                    first_reading = False
                    current_data = date
                if current_data == date:
                    if test:
                        print (f"data: {date} hour: {hour} power1: {pw1} power2: {pw2} \n ")
                    daily_data.append([hour, pw1, pw2])
                else:
                    daily_data.reverse()
                    break


def read_aurora(test):        # regular day reading ...

        ffile = open(r'status.pkl', 'rb')
        status = pickle.load(ffile)
        ffile.close()
        if status=="SLEEPING":    # first reading of the day....
                status = "ACTIVE"
                ffile = open(r'status.pkl', 'wb')
                pickle.dump(status, ffile)
                ffile.close()
        if test:
            record_fakeR = """
printf 'Input 1 Power               =     99.999999 W\nInput 2 Power               =     99.999999 W\n' > curRead.tmp
            """

            os.system(record_fakeR)
        else:
            readPower = './aurora -a2 -t -d0 -P100 -Y10 /dev/ttyUSB0 > curRead.tmp'
            os.system(readPower)
            time.sleep(2)

        # log power...
        extractData='grep "date\|1[[:blank:]]Power\|2[[:blank:]]Power" curRead.tmp >> aurora.log'
        os.system(extractData)

        # ... get numeric values to print current productio ...
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

        # and get info to plot daily data
        daily_data=[]
        actual_prod_data(test)

        if test:
            ffile = open('index.html', 'w')
        else:
            ffile = open('/var/www/html/index.html', 'w')

        Show_data(power, ffile, currTime_str, daily_data)
        ffile.close()


def lock_reading_aurora(test):

    ffile = open(r'status.pkl', 'rb')
    status = pickle.load(ffile)
    ffile.close()
    if status=="ACTIVE":    # first night op ...
            status = "SLEEPING"
            ffile = open(r'status.pkl', 'wb')
            pickle.dump(status, ffile)
            ffile.close()
            printMarker='printf "night: no reading\n\n\n"  >> aurora.log'    # ... so record it
            os.system(printMarker)

            actual_prod_data(test)

            if test:
                ffile = open('index.html', 'w')
            else:
                ffile = open('/var/www/html/index.html', 'w')
            Show_data([0, 0], ffile, "night time", daily_data)
            ffile.close()








if __name__ == "__main__":

    for arg in sys.argv[1:2]:
        test = strtobool(arg)

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

    if ((timeMin > sunRiseMin) and (timeMin <= (sunSetMin+twilightTime)) or (test)):    # daytime... or test
        read_aurora(test)
    else:
        lock_reading_aurora(test)
