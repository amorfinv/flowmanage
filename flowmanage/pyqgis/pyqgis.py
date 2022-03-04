import flowmanage as fm
try:
    from qgis.core import QgsApplication
except ImportError:
    fm.con.print('[bold red]QGIS not found!!')
    fm.con.print('[bold red]Activate [bold magenta] [light_sea_green on grey27] qgis 🅒 ')
    exit()
from flowmanage.pyqgis.qgisalgos import QgisAlgos

def start():
    # Supply path to qgis install location
    QgsApplication.setPrefixPath(fm.settings.qgis_path, True)

    # import processing to make qgis algirithms available
    from processing.core.Processing import Processing

    # Initialize QGIS application with no GUI
    qgs = QgsApplication([], True)
    qgs.initQgis()

    # initialize processing algorithms and then import them as global variables
    Processing.initialize()
    from qgis import processing 

    qgis_algos = QgisAlgos(processing)
    
    # run the algorithms specified in the settings
    for func in qgis_algos.qgis_funcs:
        if func.__name__ in fm.settings.qgis_algos:
            # run the function
            func()
            
    # exit qgis
    qgs.exitQgis()