import re
import aprslib
import requests

callsign = 'YOUR_APRSIS_CALLSIGN'
send_to = 'YOUR_APRS_CALLSIGN_TO_SEND_TO_WITH_SSID'
aprs_passcode = 'YOUR_APRSIS_PASSCODE'
mmdvm_ip = 'FULL URL TO YOUR MMDVM'
pager_id = 'YOUR PAGER ID'

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
    old_value, value = value, checkMSG()
    if value != old_value:
        print("Forwarding to APRS: " + checkMSG())
        AIS = aprslib.IS(callsign, aprs_passcode, port=14580)
        AIS.connect()
        AIS.sendall("DAPNET>APRS,TCPIP*::" + send_to.ljust(9) + ":" + checkMSG())
