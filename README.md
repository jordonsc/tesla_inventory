Tesla Inventory Notification Service
====================================
Examines current Tesla inventory and provides alerts when new vehicles are matched.

Usage:

    tesla-inv [-h] [-k MARKET] [-r REGION] -m MODEL [-t TRIM] [-c CONDITION]

          -k MARKET, --market MARKET
                                Search market; default "AU"

          -r REGION, --region REGION
                                Market sub-region; eg "Victoria"

          -m MODEL, --model MODEL
                                Vehicle model
                                Valid options: M3, MS, MY, MY

          -t TRIM, --trim TRIM  
                                Vehicle trim, comma delimited (optional) 
                                Valid options: M3RWD, SRRWD, LRAWD, PAWD

          -c CONDITION, --condition CONDITION
                                "new" or "used"; default "new"

          -a ARN
                                AWS SNS topic ARN; required

For command-line options, use:

    tesla-inv --help

Example:

    tesla-inv -k "AU" -r "Victoria" -m "MY" -t "LRAWD,PAWD" -c "new" -a "..."

Will search for all new AWD (long range & performance) Model Y vehicles in Victoria, Australia.
