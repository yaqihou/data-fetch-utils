
import os
import datetime as dt
from argparse import ArgumentParser

from src.driver import MyDriver
from src.utils import parse_str_date
from src.aa_flight_checker import AAFlightChecker

parser = ArgumentParser()
parser.add_argument('-f', '--from', '--origin',
                    nargs=1, required=True, help="Origin airport code", dest="from_airport")
parser.add_argument('-t', '--to', '--dest',
                    nargs=1, required=True, help="Origin airport code", dest="dest_airport")

parser.add_argument('-d', '--depart', default="Next Wed", type=str, nargs='?', dest="depart_date",
                    help="Depart date in format mm/dd/yyyy or natural language")
parser.add_argument('-r', '--return', default="Next tue", type=str, nargs='?', dest="return_date",
                    help="Return date in format mm/dd/yyyy or natural language (w.r.t. depart_date)")
parser.add_argument('--repeat-interval', default=7, type=int, nargs='?',
                    help=("Used together with --repeat to seach for the next few <interval>"))
parser.add_argument('--repeat', default=1, type=int, nargs='?',
                    help=("Used together with --repeat-interval to search for next few dates"
                          " with interval <interval>"))

parser.add_argument('--notify', action="store_true", help='Send notification when results are ready')
# parser.add_argument('--export-pkl', nargs='?', default=False, type=str,
parser.add_argument('--no-export-pkl', action="store_true",
                    help="Do not savee fights info as PKL file")
parser.add_argument('--pkl-save-folder', type=str, nargs=1,
                    default=os.path.join(str(os.getenv('HOME')), 'Data/AA-Flights/pkl'),
                    help="Folder to save pkl files")

parser.add_argument('--no-export-txt', action="store_true",
                    help="Do not save fights info as TXT file")
parser.add_argument('--txt-save-folder', type=str, nargs=1,
                    default=os.path.join(str(os.getenv('HOME')), 'Data/AA-Flights/txt'),
                    help="Folder to save txt files")

parser.add_argument('--no-export-tsv', action="store_true",
                    help="Do not save fights info as TSV file")
parser.add_argument('--tsv-save-folder', type=str, nargs=1,
                    default=os.path.join(str(os.getenv('HOME')), 'Data/AA-Flights/tsv'),
                    help="Folder to save tsv files")

args = parser.parse_args()
    
# Run for next 6 weeks
from_airport = args.from_airport[0]
dest_airport = args.dest_airport[0]

depart_date = parse_str_date(args.depart_date)
return_date = parse_str_date(args.return_date, source_date=depart_date)

with MyDriver() as driver:
    for _ in range(args.repeat):
        checker = AAFlightChecker(from_airport, dest_airport, depart_date, return_date, driver=driver)
        checker.run()

        if not args.no_export_pkl:
            checker.dump_pkl(save_folder=args.pkl_save_folder[0])

        if not args.no_export_txt:
            checker.dump_txt(save_folder=args.txt_save_folder[0])

        if not args.no_export_tsv:
            checker.dump_tsv(save_folder=args.tsv_save_folder[0])

        if args.notify:
            checker.send_notification()

        depart_date = depart_date + dt.timedelta(args.repeat_interval)
        return_date = return_date + dt.timedelta(args.repeat_interval)

