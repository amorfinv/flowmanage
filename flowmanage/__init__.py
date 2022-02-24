from flowmanage import settings
from rich.console import Console

# Main objects
air = None
inten = None
scen = None

# printing objects
con = Console()


def init(mode='all') -> None:

    # Initialize global settings
    settings.init()
    global air, inten, scen

    if mode == 'airspace':
        from flowmanage.airspacedesign import AirspaceDesign
        air = AirspaceDesign()

    elif mode == 'intention':

        from flowmanage.intentionmaker import IntentionMaker
        inten = IntentionMaker()

    elif mode == 'scenario':

        from flowmanage.scenariomaker import ScenarioMaker         
        scen = ScenarioMaker()

    else:
        from flowmanage.airspacedesign import AirspaceDesign 
        from flowmanage.intentionmaker import IntentionMaker
        from flowmanage.scenariomaker import ScenarioMaker

        air = AirspaceDesign()
        inten = IntentionMaker()
        scen = ScenarioMaker()