""" Main FlowManage start script """
import sys
import flowmanage as fm

def main():
    """
    """
    # Parse command-line arguments
    if '--help' in sys.argv:
        fm.con.print("[blue underline]Usage[/][blue]: [green]python FlowManage.py --options")
        fm.con.print("\n[magenta]FlowManage will run all modules in order if no options are specified.")
        fm.con.print("[magenta]The order of modules is: (1)intention, (2)airspace, (3)scenario.")
        fm.con.print("\n[red underline]Options:")
        fm.con.print("[red]--help                Display this information.")
        fm.con.print("[red]--intention           Create the intention csv files.")
        fm.con.print("[red]--airspace            Create the airspace json files.")
        fm.con.print("[red]--scenario            Create the scenario scn files.")
        fm.con.print("[red]--multi num_workers   Multiprocessing option with workers.")
        quit()  
    
    if '--airspace' in sys.argv:
        mode = 'airspace'
    elif '--intention' in sys.argv:
        mode = 'intention'
    elif '--scenario' in sys.argv:
        mode = 'scenario'
    else:
        mode = 'all'

    if '--multi' in sys.argv:
        try:
            multi = int(sys.argv[sys.argv.index('--multi') + 1])
        except IndexError:
            multi = 6
            fm.con.print("[magenta]No number of workers specified. Using default of 6.")

    # Initialize necessary modules
    fm.init(mode)

    # run the selected modules
    if mode == 'intention':
        fm.inten.process()

    elif mode == 'airspace':
        fm.air.process()

    elif mode == 'scenario':
        fm.scen.process(multi)

    else:
        fm.inten.process()
        fm.air.process()
        fm.scen.process(multi)
    

if __name__ == "__main__":
    main()
