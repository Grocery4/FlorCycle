# FlorCycle, a free web-based cycle tracker
*Project developed for educational purposes as part of the WEBTECH course at the University of Modena and Reggio Emilia.*

## Overview
The application is presented as a free, ad-free alternative to existing commercial applications for tracking the menstrual cycle.
The app has been developed as a webapp using the **Django framework**, and interacts with a **relational database** (sqlite3) to store and manage user data.

---

## Key features

### Guest mode

A simple cycle calculator for visitors aimed to predict an approximate time frame of the next menstrual cycle on-the-go, based on https://www.calculator.net/period-calculator.html

### Logged users

The core of the webapp, consisting of a dashboard in which the most relevant data is readily displayed.
Logged users are able to perform CRUD operations on menstrual cycle data and log symptoms and notes on a day-to-day basis, making predictions for the next cycles more accurate.

Users are also able to view a history of all logged cycle windows and notes thanks to a database integration, making all the information stored server-side persistent.

### Partner mode

The webapp provides the users with a 'partner-mode': a read-only view of a period-haver's dashboard and stats.

### Forums & Community

Premium users will have access to an additional forum to consult with professional figures approved by the moderators through a thorough inspection of their credentials.

---

## Misc

### Notifications

The webapp is equipped with a notification module which will alert the user in case of dangerous symptoms and before the start of a menstruation/ovulation window.

### Language support

Currently, the webapp supports the English and Italian languages.
As of now, no plan on expanding it further has been made.

---

## Installation

To run the webapp `python3.12` and `pipenv` are necessary.

1. git clone the repo in a directory
2. to install the required libraries run:

```
pipenv install Pipfile
```

3. once the installation is complete, to initialize the database, from the root directory run:

```
> python3 project/manage.py makemigrations
> python3 project/manage.py migrate
``` 

4. finally:

```
python3 project/manage.py runserver
```

---

## Admin page

An additional admin page can be accessed through the url http://localhost:8000/admin. To create a superuser just run `python3 project/manage.py createsuperuser` and fill in the form.

To further analyze the models in the webapp, it might be necessary to register them from the admin.py of the relevant module.

``` admin.py
from django.contrib import admin
from .models import <Model>

admin.site.register(Model)
```
