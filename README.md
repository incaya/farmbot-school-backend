# Python API to use Farmbot in *multi-user* context

API built with [flask](https://flask.palletsprojects.com/en/1.1.x/) RESTFul toolkits (see requirements.txt root file for more informations).

Only available with python3

## To install & configure it

> clone the repo
>
> on the root folder, execute `pip3 -r requirements.txt` to install Python required packages
>
> create a copy of `config.json.example`, rename it `config.json` and put your config

## To create database and a user admin

> `cd db`
>
> `flask db upgrade`
>
> `python create_admin.py`

## To execute API test

> in project root folder, execute `make test`
>
> to execute test for only one resource `make test res=name_of_res`

## To run the API

> `flask run`

## Access API Doc

> Go to [http://localhost:5000](http://localhost:5000)

## Documentation

https://www.farmbot-school.fr/

## Credits & contributors

This repository is part of Normandy Farmbot project :

- funded by **EU (FEDER)** and **Région Normandie**
- led by **Chambre Régionale d'Agriculture de Normandie** and **Le Dôme** (Caen, France)

This application was initially developed by [INCAYA](https://www.incaya.fr)

## Licence

GPL v3, cf. COPYING