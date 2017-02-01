# DjangoCRM

## Description

- Stores developers of a particular organization, being able to assign projects and status to each one of them, as well as working hours.
- Integrated with Github and Asana. Sends invitations to a new dev to organizations and revokes permissions in case they become inactive.
- Checks all commits done by users in search of #time tag. In case it founds one it counts the amount of hours a dev worked in each project.

## Prerequisites

- Virtualenv
- Github User
- Github Organization
- Github Personal Access Token
- Asana User
- Asana Access Token

You are requiered to have permissions to Github **and** Asana to have full access of the app.
If you don't you can leave them blank but some features will fail.

### Pip, Postgres Libs, Psql

```
sudo apt-get update
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib
```

## Instalation

### Create database and user

```
sudo su - postgres
psql
CREATE DATABASE django_crm;
CREATE USER select_user WITH PASSWORD 'select_password';
GRANT ALL PRIVILEGES ON DATABASE django_crm TO select_user;
\q
exit
```

### VirtualEnv

- Create a new virtual environment
- pip install -r requirements.txt
- edit bin/activate to (Please change all data to your personal one):

For Production/Deploy and Develop:

```
SECRET_KEY='6!918+lne$pvkoao4vbhzs_&4dv&4p=l6ycf9+))k#+er)&o(w'
export SECRET_KEY

DBUSER='select_user'
export DBUSER

DBPASSWORD='select_password'
export DBPASSWORD

GIT_USER=''
export GIT_USER

GIT_ORGANIZATION='onitsoft'
export GIT_ORGANIZATION

GIT_ACCESS_TOKEN=''
export GIT_ACCESS_TOKEN

ASANA_USER=''
export ASANA_USER

ASANA_ACCESS_TOKEN=''
export ASANA_ACCESS_TOKEN
```

For production/deploy:

```
DJANGO_SETTINGS_MODULE="karinacms.settings_prod"
export DJANGO_SETTINGS_MODULE
```
