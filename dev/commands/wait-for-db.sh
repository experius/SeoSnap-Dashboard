#!/bin/bash
RET=124
until [ ${RET} -ne 124 ]; do
  bash dev/commands/wait-for-it.sh $DB_HOST_OVERRIDE:3306 -t 3 -s -- $@
  RET=$?
done
