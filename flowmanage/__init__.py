from flowmanage import settings
from rich.console import Console

# Main objects
air = None
inten = None
scen = None
pyqgis = None

# printing objects
con = Console()


def init(mode='all') -> None:

    # Initialize global settings
    settings.init()
    global air, inten, scen, odpoints, pyqgis

    if mode == 'airspace':
        from flowmanage.airspacedesign import AirspaceDesign
        air = AirspaceDesign()

    elif mode == 'intention':

        from flowmanage.intentionmaker import IntentionMaker
        inten = IntentionMaker()

    elif mode == 'scenario':

        from flowmanage.scenariomaker import ScenarioMaker         
        scen = ScenarioMaker()

    elif mode == 'odpoints':
        """This is only used if specified in the command line"""

        from flowmanage.odpoints import StreetCenterPoints
        odpoints = StreetCenterPoints()
    
    elif mode == 'qgis':
        """This is only used if specified in the command line"""
        # this runs the algorithms in qgis
        import flowmanage.pyqgis

    else:
        from flowmanage.airspacedesign import AirspaceDesign 
        from flowmanage.intentionmaker import IntentionMaker
        from flowmanage.scenariomaker import ScenarioMaker

        air = AirspaceDesign()
        inten = IntentionMaker()
        scen = ScenarioMaker()