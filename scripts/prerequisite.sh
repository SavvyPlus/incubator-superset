sudo apt-get update

sudo apt-get install python3.6
sudo ln -sT /usr/bin/python3 /usr/bin/python

sudo apt-get install python3-pip -y
sudo ln -sT /usr/bin/pip3 /usr/bin/pip

curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
sudo apt-get install -y nodejs

sudo apt install default-jre -y
sudo apt install openjdk-8-jre-headless 

sudo apt install -y python3-venv 

pip install --upgrade --user awscli
export PATH=/home/ubuntu/.local/bin:$PATH

sudo apt-get install redis-server -y