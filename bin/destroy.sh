#!/bin/bash -e

usage()
{
    echo -e "\nUsage: $(basename $0) [--silent,-s <auto approve terraform destroy (default = prompt for approval)>]"
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

pushd ../terraform > /dev/null

if [ "$silent" = true  ]; then
       terraform destroy -auto-approve
else 
       terraform destroy
fi 

popd > /dev/null
