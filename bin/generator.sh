#!/bin/bash -e
#
# Generate the synthetic input trades serially
#
CONFIG="../config/azfinsim.config"
if [ -f $CONFIG ]; then
   source $CONFIG
else
   echo "ERROR: Configuration file $CONFIG does not exist. You must first generate a configuration file by running ./deploy.sh"
   echo "(The redis cache needs to be created before you can inject the trade data)"
   exit 1
fi


usage()
{
    echo -e "\nUsage: $(basename $0) [--silent,-s <don't echo the trades to the terminal; default = echo)>]"
    exit 1
} 

silent=false
while [[ $# -gt 0 ]]
do
   key="$1"
   case $key in
      -s|--silent)
         silent=true
         shift;
      ;;
      *)
         usage
         shift;
      ;;
   esac
done

if [ "$silent" = true ]; then 
   ../src/generator.py --threads 64 --start-trade 0 --trade-window 1000000 --cache-type redis --cache-name $AZFINSIM_REDISHOST --cache-port $AZFINSIM_REDISPORT --cache-ssl yes --format eyxml --verbose false 
else 
   ../src/generator.py --threads 64 --start-trade 0 --trade-window 1000000 --cache-type redis --cache-name $AZFINSIM_REDISHOST --cache-port $AZFINSIM_REDISPORT --cache-ssl yes --format eyxml --verbose true
fi 
