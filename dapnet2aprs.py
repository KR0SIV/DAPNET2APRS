import re
import aprslib
import requests
import time

callsign = 'YOUR_APRSIS_CALLSIGN'
send_to = 'YOUR_APRS_CALLSIGN_TO_SEND_TO_WITH_SSID'
aprs_passcode = 'YOUR_APRSIS_PASSCODE'
mmdvm_ip = 'FULL URL TO YOUR MMDVM'
pager_id = 'YOUR PAGER ID'
waitTime = 60 #Your delay in seconds between message checks, let's not hammer the crap out of the MMDVM hum?

def checkMSG():

    r = requests.get(mmdvm_ip)

    strip1 = re.findall("!important;.>\w{4,9}:\s[\w\s]{2,69}", str(r.content))
    try:
        messageContent = re.sub('!important;.>', '', str(strip1[0]))
        return messageContent
    except:
        pass

value = 0
while True:
    print('Waiting for ' + str(waitTime) + ' seconds to be nice')
    time.sleep(waitTime)
    old_value, value = value, checkMSG()
    if value != old_value:
        try:
            print("Forwarding to APRS: " + checkMSG())
            AIS = aprslib.IS(callsign, aprs_passcode, port=14580)
            AIS.connect()
            AIS.sendall("DAPNET>APRS,TCPIP*::" + send_to.ljust(9) + ":" + checkMSG())
        except:
            pass
    else:
        print('No new messages')
