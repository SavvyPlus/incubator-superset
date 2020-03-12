upgrade_db=$1
init_ss=$2

cd /home/ubuntu/incubator-superset

. /home/ubuntu/incubator-superset/venv/bin/activate
python --version

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

if [ $upgrade_db = "true" ]
then
  superset db upgrade
fi

if [ $init_ss = "true" ]
then
  superset init
fi
