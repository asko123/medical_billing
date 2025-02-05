#!/bin/bash

echo "..TRAI ETL.."
echo "The env you are in is:"
echo "$1"

# setting environment settings


# current_path=`dirname "$0"`
hostname=$(hostname)

current_path=$(pwd)
cd ..
root_path=$(pwd)

echo "$0"
cd "$current_path"
echo "the current path"
echo "$current_path"

echo "$root_path"

# setting up the virtual env folder
if [ ! -e "/local/scratch/virtualenv" ]
then
    mkdir /local/scratch/virtualenv/
    chmod -R +rwx /local/scratch/virtualenv/
fi

pushd /local/scratch/virtualenv/

chmod -R +rwx /local/scratch/virtualenv/
chmod -R 777 /local/scratch/virtualenv/

# creating the python 3.8 virtualenv
if [ ! -e "/local/scratch/virtualenv" ]
then
    echo "Building virtual environment"
    /sw/external/python-3.8.12/bin/python3 -m venv virtualenv --symlinks
fi

execute_code="$root_path/etl/main.py"

echo "The execute path"
echo "$execute_code"
cd "$current_path"

unset PYTHONPATH
unset PYTHONHOME

source /local/scratch/virtualenv/virtualenv/bin/activate
PATH=/local/scratch/virtualenv/virtualenv/bin:$PATH

export PATH
echo "$PATH"
which python
python --version

## To prove we're in the virtual env
echo "python path"
which pip
pip -V

# setting up the code execution for python and for spark home
export PYTHONPATH=/local/scratch/virtualenv/virtualenv/bin/

# pip install the required libs
pip install --upgrade pip
pip install --upgrade setuptools
pip install requests
pip install PyYAML
pip install requests_gssapi
pip install pandas
pip install numpy
pip install gs-auth
pip install aiohttp
pip install asyncio
pip install boto3
pip install botocore
pip install PyPDF2
pip install Python-IO
pip install requests-ntlm
pip install requests-toolbelt

chmod u+w /var/cv/dev_pranalytics/creds/caf1735704434271a295b324fcf0e746
keytab_path=/var/cv/dev_pranalytics/creds/caf1735704434271a295b324fcf0e746
export KRB5CCNAME=$krb
kinit $execution_user -k -t "$keytab_path"

# Log the environment being used
echo "Launching ETL in environment: $1"

python "$execute_code" "$1"

deactivate

rm -rf /local/scratch/virtualenv.tar.gz
rm -rf /local/scratch/virtualenv

