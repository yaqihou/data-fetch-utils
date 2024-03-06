# Data Fetching Utilities Collection

This repository stores a collection of scripts I used to fetch data from WWW.

Disclaimer: all scripts here are just to make my life easier, and nothing was intended to be used as web crawler or for large-scale data fetching. 

All scripts tested under Ubuntu 22.04, Python 3.10.


## Scripts and Usage Case

### Flight Price Check

Limitations:
- Occasionally fail to load the results, so that some hard-coded refresh is used as a workaround. Will fetch the results eventually in most of time, just the process looks nasty
- Only fetch the price on the depart screen, i.e. shows only the lowest price
- Only implemented for AA

```
usage: check_aa_flight.py [-h] -f FROM_AIRPORT -t DEST_AIRPORT [-d [DEPART_DATE]] [-r [RETURN_DATE]] [--repeat-interval [REPEAT_INTERVAL]] [--repeat [REPEAT]] [--notify] [--no-export-pkl] [--pkl-save-folder PKL_SAVE_FOLDER]
                          [--no-export-txt] [--txt-save-folder TXT_SAVE_FOLDER] [--no-export-tsv] [--tsv-save-folder TSV_SAVE_FOLDER]

options:
  -h, --help            show this help message and exit
  -f FROM_AIRPORT, --from FROM_AIRPORT, --origin FROM_AIRPORT
                        Origin airport code
  -t DEST_AIRPORT, --to DEST_AIRPORT, --dest DEST_AIRPORT
                        Origin airport code
  -d [DEPART_DATE], --depart [DEPART_DATE]
                        Depart date in format mm/dd/yyyy or natural language
  -r [RETURN_DATE], --return [RETURN_DATE]
                        Return date in format mm/dd/yyyy or natural language (w.r.t. depart_date)
  --repeat-interval [REPEAT_INTERVAL]
                        Used together with --repeat to seach for the next few <interval>
  --repeat [REPEAT]     Used together with --repeat-interval to search for next few dates with interval <interval>
  --notify              Send notification when results are ready
  --no-export-pkl       Do not savee fights info as PKL file
  --pkl-save-folder PKL_SAVE_FOLDER
                        Folder to save pkl files
  --no-export-txt       Do not save fights info as TXT file
  --txt-save-folder TXT_SAVE_FOLDER
                        Folder to save txt files
  --no-export-tsv       Do not save fights info as TSV file
  --tsv-save-folder TSV_SAVE_FOLDER
                        Folder to save tsv files
```

For example, assuming that I could like to travel on Wed and return the next Tue after my departure, and I wanted to check for the next 10 weeks for the price. The command is as below:

```bash
python3 check_aa_flight.py -f AAA -t BBB -d "next wed" -r "next Tue" --repeat 10 --repeat-interval 7
```
