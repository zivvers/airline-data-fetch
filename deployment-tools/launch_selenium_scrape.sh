#!/bin/bash
#================================================
#
#  this script launches the danielfrg/selenium
#  docker image (a selenium browser), waits for
#  it to be ready for use and then deploys
#  a python scraping script
#
#================================================
# abort script if any command returns non-zero
set -e 
# make sure we have danielfrg/selenium image locally
# if we get non-error output from this docker command then 
# we know we have the image locally
if [[ "$(sudo docker images -q danielfrg/selenium 2> /dev/null)" == "" ]]; then
    echo "danielfrg/selenium not available locally" 1>&2
    exit 1
fi

# ok now check if we're currently running danielfrg/selenium container 
# if not, launch danielfrg/selenium image as a detached container
# (or else we'll get dropped into container's shell)
# don't want to see stdout

if [[ "$(sudo docker ps -q -f ancestor=danielfrg/selenium)" == "" ]]; then
    echo "Starting Selenium container..."
    sudo docker run -d -v /dev/shm:/dev/shm -p 4444:4444 danielfrg/selenium > /dev/null
else
    echo "Selenium container already running"
fi

# get (most recent) container ID
CONTAINER="$(sudo docker ps -q -f ancestor=danielfrg/selenium)"

# pipe output of docker logs (which normally only goes to stderr)
# into file descriptor, BUT kill after a minute
# run `sed` command to find either 'Selenium Server is up and running' or 'TERMINATED' and print
# first match and then quit
# notice that unlike how suggested at `https://stackoverflow.com/questions/21001220/bash-sequence-wait-for-output-then-start-next-program` we do not `cat <&3` or else will print our `timeout` kill output
exec 3< <(timeout -k 2m 2m sudo docker logs -f $CONTAINER 2>&1 || ([[ $? -eq 137 || $? -eq 124 ]] && echo TERMINATED))
PID=$! #get PID to kill above process before we exit
OUTPUT=`sed -n "/.*\(Selenium Server is up and running$\|TERMINATED$\).*/{s//\1/p;q}" <&3`

# if we terminated before Selenium ready exit w/ failure
if [[ "$OUTPUT" == "TERMINATED" ]]; then
    echo "Unsuccessful Selenium boot...killing container"
    kill -9 $PID
    sudo docker kill $CONTAINER
    exit 1

elif [[ "$OUTPUT" == "Selenium Server is up and running" ]]; then
    echo "Successful Boot"
    # KILL our docker log process or else it gets terminated after script finishes
    #kill -9 $PID1
    kill -9 $PID

else 
    echo "unmatched value from OUTPUT variable"
fi

# get IPAddress of our Selenium container
IPAddress=`sudo docker inspect $CONTAINER | grep -wm1 IPAddress | cut -d '"' -f 4`
# manual process to build connection address should in future
# be replaced with process to find "20:09:25.026 INFO - RemoteWebDriver instances should connect to: http://127.0.0.1:4444/wd/hub"
# an extract address
IPAddress="$IPAddress:4444/wd/hub"
echo $IPAddress

python southwest-scrape-tools.py $IPAddress
