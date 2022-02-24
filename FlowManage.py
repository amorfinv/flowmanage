""" Main FlowManage start script """
import sys
import flowmanage as fm

def main():
    """
    """
    # Parse command-line arguments
    if '--help' in sys.argv:
        fm.con.print("[blue underline]Usage:[/] [green]python FlowManage.py --options")
        fm.con.print("\n[magenta]FlowManage will run all modules in order if no options are specified.")
        fm.con.print("[magenta]The order of modules is: (1)intention, (2)scenario, (3) airspace.")
        fm.con.print("\n[red underline]Options:")
        fm.con.print("[red]--help               Display this information.")
        fm.con.print("[red]--airspace           Create the airspace json files.")
        fm.con.print("[red]--intention          Create the intention csv files.")
        fm.con.print("[red]--scenario           Create the scenario scn files.")
        quit()  
    
    if '--airspace' in sys.argv:
        mode = 'airspace'
    elif '--intention' in sys.argv:
        mode = 'intention'
    elif '--scenario' in sys.argv:
        mode = 'scenario'
    else:
        mode = 'all'


    # Initialize necessary modules
    fm.init(mode)

    # run the selected modules
    if mode == 'airspace':
        fm.air

    elif mode == 'intention':
        fm.inten

    elif mode == 'scenario':
        fm.scen

    else:
        fm.air
        fm.inten
        fm.scen
    

if __name__ == "__main__":
    main()
