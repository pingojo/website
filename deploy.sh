#!/bin/bash

STORAGE_DIR=/opt/render/project/.render
CHROME_DIR=$STORAGE_DIR/chrome
CHROME_BINARY_PATH=$CHROME_DIR/opt/google/chrome/google-chrome
CHROMEDRIVER_PATH=$CHROME_DIR/chromedriver

mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download and extract Google Chrome
wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x ./google-chrome-stable_current_amd64.deb $CHROME_DIR
rm ./google-chrome-stable_current_amd64.deb

# Download and extract ChromeDriver
wget -O chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
echo "Downloaded Chromedriver"
unzip chromedriver_linux64.zip
echo "Unzipped Chromedriver"
rm chromedriver_linux64.zip

# Move ChromeDriver to the Chrome directory
mv chromedriver $CHROMEDRIVER_PATH
echo "Moved Chromedriver"

# Set execute permissions on ChromeDriver
chmod +x $CHROMEDRIVER_PATH
echo "Set execute permissions on Chromedriver"

cd -

# Print the versions of Google Chrome and ChromeDriver
$CHROME_BINARY_PATH --version
$CHROMEDRIVER_PATH --version

# Install Python dependencies and prepare Django project
pip install -r requirements.txt 
python manage.py migrate --noinput 
python manage.py collectstatic --noinput 
