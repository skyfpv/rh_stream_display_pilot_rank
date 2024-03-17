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
DEBUG_LOGGING = False

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
        node_num = rhapi.race.slots
        #return render_template('pilotcard.html', __=__,)
        return render_template('ranks.html', serverInfo=None,
            getOption=rhapi.db.option, __=rhapi.__, num_nodes=node_num)
    rhapi.ui.blueprint_add(bp)
    
    log("rank stream display plugin initialized")

class RUManager():
    def __init__(self, rhapi):
        self.rhapi = rhapi
        
        #websocket listeners
        self.rhapi.ui.socket_listen("get_live_ranks", self.handleGetLiveRanks)

        #register event handlers
        self.rhapi.events.on(Evt.HEAT_SET, self.handleUpdateLiveRankings)
        self.rhapi.events.on(Evt.RACE_LAP_RECORDED, self.handleUpdateLiveRankings)

    def handleUpdateLiveRankings(self, args):
        self.handleGetLiveRanks()

    def handleGetLiveRanks(self):
        log("handleGetLiveRanks")
        
        liveRanks = []
        if(self.rhapi.race.status==RaceStatus.RACING):
            results = self.rhapi.race.results
            meta = results["meta"]
            primary_leaderboard = meta["primary_leaderboard"]
            leaderboard = results[primary_leaderboard]
            log(str(leaderboard))
            for pilotResult in leaderboard:
                liveRanks.append(self.getPilotRank(pilotResult))
        else:
            results = self.rhapi.race.results
            meta = results["meta"]
            primary_leaderboard = meta["primary_leaderboard"]
            leaderboard = results[primary_leaderboard]
            log(str(leaderboard))
            for pilotResult in leaderboard:
                liveRanks.append(self.getPilotRank(pilotResult))

        self.rhapi.ui.socket_broadcast("live_ranks", liveRanks)
            
    def getPilotRank(self, result):
        seatColor = self.rhapi.race.seat_colors[result["node"]]
        seatColor = self.colorToHex(seatColor)
        callsign = result["callsign"]
        result["color"] = seatColor
        pilotRank = result
        log(pilotRank)
        return pilotRank

    def colorToHex(self, colorInt):
        return '#' + format(colorInt, '06x')
