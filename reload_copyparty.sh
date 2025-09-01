COPYPARTYPID=$(docker inspect -f '{{.State.Pid}}' copyparty)
kill -s USR1 $COPYPARTYPID