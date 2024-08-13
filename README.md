# Python Django Server

## Setting up Your Environment

It is recommended that you use a local vitual environment to setup your envrionemtn and install packages


### Setting up a Virtual Environment

Run the command below to create a virtual environment for your project in the root directory of your project. 

You will only have to run this command the first time to set up your virtual environment.

```
python -m venv myproject
```

<br>
Run the command below to activate the virtual environment everytime you start working. It is recommended that you install necessary packages in the virtual environment as well.

<br>

```
source myproject/bin/activate
```

Note: You must be in the directory that contains your virtual environment folder in order to be able to activate it everytime before you start your workflow.
<br>

You can exit your virtual envrionment by running the following command:

```
deactivate
```
<br>

### Installing Necessary Packages

Start up your virutal envrionment before installing packages. Refer to the instructions in this section to start your virtual environment

Run the commands below to install required packages from [requirements.txt](requirements.txt)

```
sudo apt-get install libpq-dev
pip install -r requirements.txt
```
Please note that psycopg2 package could throw errors when trying to installing it in a virtual environment. If this si the case, please install psycopg2 package outside of the virtual environment first before installing the rest of the of required packages inside the virtual environment.

## Run Backend Server
Please note that you will have to run the backend server before you run the front end server which located in a different folder.

```
python manage.py migrate
```

## Create Cache DB for dev
```
python manage.py createcachetable
```
