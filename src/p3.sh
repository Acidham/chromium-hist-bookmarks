#!/bin/bash
PREFER_LATEST=1

#Array of python3 paths
PYPATHS=(/usr/bin /usr/local/bin)

SCR="${1}"
QUERY="${2}"
WF_DATA_DIR=$alfred_workflow_data

#Create wf data dir if not available
[ ! -d "$WF_DATA_DIR" ] && mkdir "$WF_DATA_DIR"

SCRPATH="$0"
SCRIPT_DIR="$(dirname $SCRPATH)"

#in case not running from alfred
[ -z "$SCRIPT_DIR" ] && SCRIPT_DIR=.

#Cache file for python binary - we use this to prevent reevaluation on each script run
PYALIAS="$WF_DATA_DIR/py3"


CONFIG_PREFIX="Config"
# RERUN=0
DEBUG=0


pyrun() {
  $py3 "${SCR}" "${QUERY}"
  RES=$?
  [[ $RES -eq 127 ]] && handle_py_notfound
  return $RES
}

handle_py_notfound() {
  #we need this in case of some OS reconfiguration , python3 uninstalled ,etc..

  if [[ $RERUN -eq 1 ]]
  then
    #Already tried reconfigure, unknown error
    log_msg "Could not configure python3, please check manualy configure at $PYALIAS"
    exit 255
  fi
  log_debug "python3 configuration changed, attemping to reconfigure"
  setup_python_alias

  #attempt rerun
  # RERUN=1
}

verify_not_stub() {
  PYBIN="{$1}"
  $PYBIN -V > /dev/null 2>&1
}

getver() {
  PYBIN="${1}"
  #Extract version info and convert to comparable decimal
  VER=$($PYBIN -V |  cut -f2 -d" " | sed -E 's/\.([0-9]+)$/\1/')
  echo $VER
  log_debug "Version: $VER"
}

make_alias() {
  PYBIN="${1}"
  PYVER="$2"
  #sanitize
  [ "${PYBIN}" = "" ] && log_msg "Error: invalid python3 path" && exit 255
  echo "export py3='$PYBIN'" > "$PYALIAS"
  log_msg "Python3 was found at $PYBIN." "Version: $PYVER, Proceed typing query or re-run worfklow"
}

log_msg() {
  log_json "$CONFIG_PREFIX: $1" "$2"
  log_debug "$1"
}

log_json() {
#need to use json for notifications since we're in script filter
title="$1"
sub="$2"
[ -z "$sub" ] && sub="$title"
cat <<EOF
{
    "items": [
        {
            "title": "$title",
            "subtitle": "$sub",
            "valid": "False",
        }
    ]
}
EOF
}

log_debug() {
  [[ $DEBUG -eq 1 ]] && echo "DEBUG: $*" >&2
}

setup_python_alias() {
  current_py=""
  current_ver=0.00
  for p in "${PYPATHS[@]}"
  do
    if [ -f $p/python3 ]
    then
      #check path does not contain a stub
      [[ $(verify_not_stub "$p/python3") -ne 0 ]] && continue

      #check for latest py3 version
      if [ $PREFER_LATEST -eq 1 ]
      then
        thisver=$(getver $p/python3)
        if  [[ $(echo "$thisver > $current_ver" | bc -l) -eq 1 ]]
        then
          current_ver=$thisver
          current_py=$p/python3
        fi
      else
        #Just take the first valid python3 found
        make_alias $p/python3
        break
      fi
    fi
  done
  if [ $current_ver = 0.00 ]
  then
    log_msg "Error: no valid python3 version found"
    exit 255
  fi
  make_alias "$current_py" "$current_ver"
  . $PYALIAS
}

#Main
if [ -f "$PYALIAS" ]
then
  . "$PYALIAS"
  pyrun
  exit
else
  setup_python_alias
  # pyrun
fi

