from libs.arguments import args

from libs.Garden import Garden

def main():
    # Main execution
    with Garden(system=args.system, age=args.age, config_file=args.config) as garden:
        garden.tend()

if __name__ == "__main__":
    main()
