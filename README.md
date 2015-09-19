# igem-wiki-wizard
This is the igem-wiki-wizard software developed by the iGEM Team DTU-Denmark in 2015. It can be used to build and upload iGEM wikis.
The software provides an administration panel with WYSIWYG text editing of content, and syntax highlighted editors for html, javascript and css files.
Comes with a default layout that shows some of the features.

## Requirements
[Python](http://www.python.org) (2.7)

SQLite (locally) or MySQL (OpenShift)

## Local Server
To easily install the needed requirements using pip:

    pip install -r requirements.txt

Start a local server by running:

    python manage.py runserver

The server will run on [http://localhost:5000](http://localhost:5000)

##Deploy on OpenShift
To deploy a clone of this application using the [`rhc` command line tool](http://rubygems.org/gems/rhc):

    rhc app create wikiwizard python-2.7 mysql-5.1 --from-code=https://github.com/dkmva/igem-wiki-wizard.git
  
Or [link to a web-based clone+deploy](https://openshift.redhat.com/app/console/application_type/custom?cartridges%5B%5D=python-2.7&cartridges%5B%5D=mysql-5.1&initial_git_url=https://github.com/dkmva/igem-wiki-wizard.git) on [OpenShift Online](http://OpenShift.com): 

    https://openshift.redhat.com/app/console/application_type/custom?cartridges%5B%5D=python-2.7&cartridges%5B%5D=mysql-5.1&initial_git_url=https://github.com/dkmva/igem-wiki-wizard.git
