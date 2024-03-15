import logging
from RHUI import UIField, UIFieldType, UIFieldSelectOption
import struct
from time import monotonic
from Database import ProgramMethod
from RHRace import RaceStatus
from flask.blueprints import Blueprint
from flask import Flask, templating
from eventmanager import Evt
import re

def __(str):
    return ""

logger = logging.getLogger(__name__)

#Logging
DEBUG_LOGGING = True

def log(message):
    if(DEBUG_LOGGING):
        logging.info(str(message))
    else:
        logging.debug(str(message))

def render_template(template_name_or_list, **context):
    try:
        return templating.render_template(template_name_or_list, **context)
    except Exception:
        logger.exception("Exception in render_template")
    return "Error rendering template"

def initialize(rhapi):
    RH = RUManager(rhapi)

    log("initializing pilot detail plugin")

    bp = Blueprint(
        'ranks',
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/ranks/static'
    )



    #bp = Blueprint('pilotcard', __name__)
    @bp.route('/stream/ranks')
    def bp_test_page():
        node_num = 4
        #return render_template('pilotcard.html', __=__,)
        return render_template('ranks.html', serverInfo=None,
            getOption=rhapi.db.option, __=rhapi.__, num_nodes=node_num)
    rhapi.ui.blueprint_add(bp)
    
    log("rank stream display plugin initialized")

class RUManager():
    def __init__(self, rhapi):
        self.rhapi = rhapi
        
        #websocket listeners
        #self.rhapi.ui.socket_listen("get_pilot_photo", self.handleGetPilotPhoto)

    def handleGetPilotPhoto(self, args):
        log(args)
        node = int(args["node"])
        if(len(self.rhapi.race.pilots)-1>=node):
            pilotId = self.rhapi.race.pilots[node]
        else:
            pilotId = None
        self.sendPhotoURLByPilotId(pilotId, node)

    def sendPhotoURLByPilotId(self, pilotId, node):
        if(pilotId!=None):
            pilotPhotoURL = self.rhapi.db.pilot_attribute_value(pilotId, PILOT_URL_FIELD_NAME)
            secondaryColor = self.rhapi.db.pilot_attribute_value(pilotId, PILOT_SECONDARY_COLOR_FIELD_NAME)
        else:
            pilotPhotoURL = ""
            secondaryColor = "#000000"
        #if the secondary color is invalid, use the primary color
        if(self.isValidHexColor(secondaryColor)==False):
            seatColor = self.rhapi.race.seat_colors[node]
            seatColor = self.colorToHex(seatColor)
            secondaryColor = seatColor
        
        log("url: "+str(pilotPhotoURL))
        log("pilotId: "+str(pilotId))
        if(pilotId!=None and pilotId!=0):
            pilot = self.rhapi.db.pilot_by_id(pilotId)
            callsign = pilot.callsign
        else:
            callsign = None
        body = {"callsign":callsign, "url": pilotPhotoURL, "node": node, "secondaryColor": secondaryColor}
        log("-> "+str(body))
        self.rhapi.ui.socket_broadcast("pilot_photo", body)

    def colorToHex(self, colorInt):
        return '#' + format(colorInt, '06x')
    
    def isValidHex(self, string):
        pattern = re.compile(r'^[a-fA-F0-9#]+$')
        return bool(pattern.match(string))
    
    def isValidHexColor(self, color):
        valid = True
        if(color==None):
            valid = False
        else:
            if(len(color)!=7) or (self.isValidHex(color)==False):
                valid = False
        return valid
