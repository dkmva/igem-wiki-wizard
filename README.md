# igem-wiki-wizard
This is the igem-wiki-wizard software developed by the iGEM Team DTU-Denmark in 2015.
It is a content management system (CMS) for iGEM wikis. 

## Features
* Provides easy management of wiki pages and their content.
* Easy management of team members, advisors, sponsors etc.
* Content can be edited in a 'Word like' what you see is what you get editor [(CKEditor)](http://ckeditor.com).
* Wiki can be easily uploaded to iGEM servers. No need to worry about namespaces.
* Possibility to add themes and easily switch between different themes.
* Collaboration on content pages, powered by [TogetherJS](https://togetherjs.com)*



Collaboration is currently in beta, and must be enabled by the users by pressing the 'Start TogetherJs' button. 

## Requirements
[Python](http://www.python.org) (2.7)

SQLite (locally) or MySQL (OpenShift)

### Python packages

* [Flask](http://flask.pocoo.org) - Web framework
* [Flask-Admin](http://flask-admin.readthedocs.org/en/latest/) - Administration panel
* [Flask-Login](https://flask-login.readthedocs.org/en/latest/) - User login
* [Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/) - SQLAlchemy for flask
* [Flask-Themes2](https://flask-themes2.readthedocs.org) - Themes
* [Flask-WTF](http://flask-wtf.readthedocs.org/en/latest/) - Flask integration with wtforms.
* [PyYAML](http://pyyaml.org) - Used for configuration file.
* [requests](http://docs.python-requests.org/en/latest/) - HTTP requests, used to interact with iGEM servers. 
* [SQLAlchemy](http://www.sqlalchemy.org) - Python SQL toolkit
* [WTForms](http://wtforms.simplecodes.com) - Webforms


## Local Server
To easily install the needed requirements using pip:

    pip install -r requirements.txt

Start a local server by running:

    python run.py

The server will run on [http://localhost:8000](http://localhost:8000)

##Deploy on OpenShift
To deploy a clone of this application using the [`rhc` command line tool](http://rubygems.org/gems/rhc):

    rhc app create wikiwizard python-2.7 mysql-5.1 --from-code=https://github.com/dkmva/igem-wiki-wizard.git
  
Or [link to a web-based clone+deploy](https://openshift.redhat.com/app/console/application_type/custom?cartridges%5B%5D=python-2.7&cartridges%5B%5D=mysql-5.1&initial_git_url=https://github.com/dkmva/igem-wiki-wizard.git) on [OpenShift Online](http://OpenShift.com): 

    https://openshift.redhat.com/app/console/application_type/custom?cartridges%5B%5D=python-2.7&cartridges%5B%5D=mysql-5.1&initial_git_url=https://github.com/dkmva/igem-wiki-wizard.git
