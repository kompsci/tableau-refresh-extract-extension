# Tableau Refresh Extract Extension 

## POC Only

The code in this repository was developed for Tableau DataDev Day 2021. 

https://www.tableau.com/DataDevDay

It is for demonstration purposes only. 

## DESCRIPTION

Dashboard Extension + Utility that creates a Hyper Extract of Google Places Search Data. The extract is created based on the *query text* supplied. For example, when the query text 
'ice cream' is supplied, the Google Places API will return a list of places matching that search term and the new extract will contain only 'ice cream' places. 

## REQUIREMENTS

- Python 3.9+
- [Tableau Server Client](https://github.com/tableau/server-client-python)
- [Tableau Hyper API](https://help.tableau.com/current/api/hyper_api/en-us/docs/hyper_api_installing.html)
- [Tableau Extensions API](https://tableau.github.io/extensions-api/)

## INSTALLATION

After cloning the repository you will need to run this command:

``pip install -r requirements.txt``

This will install all necessary dependencies.

## HOW TO RUN THE SCRIPT

The script should be executed on the command line, using the correct command line arguments and configuration file. 

### Configuration File

The application uses a configuration file. It expects this file to be at this file path `./config/config.yaml`. 

The configuration file is what defines which Tableau Server and Tableau Site to execute the user action against. This is also where the authentication information is stored. 

The `config` directory contains a config-sample.yaml file that can be used as a template for creating a configuration file. 

The path to the configuration file can also be specified via the command line argument `-c` if you would like to reference a file in the non-default location.

```shell
python main.py -c ./config/myconfig.yaml ...
```

### Command Line Arguments

Here is the usage printout for the script describing the command line arguments. 

```sh
usage: main.py [-h] [--config-file CONFIG_FILE] --mode {export,import} [--csv-file-path CSV_FILE_PATH] [--user-auth-type {LOCAL,SAML,AD}] [--user-initial-password USER_INITIAL_PASSWORD]
               [--logging-level {debug,info,error}]

Tableau Add Users Utility

optional arguments:
  -h, --help            show this help message and exit
  --config-file CONFIG_FILE, -c CONFIG_FILE
                        configuration file for application
  --mode {export,import}, -m {export,import}
                        Script Mode
  --csv-file-path CSV_FILE_PATH, -f CSV_FILE_PATH
                        CSV File Path for Export or Import
  --user-auth-type {LOCAL,SAML,AD}, -t {LOCAL,SAML,AD}
                        Type of user being added (AD User, SAML User, Local User)
  --user-initial-password USER_INITIAL_PASSWORD, -p USER_INITIAL_PASSWORD
                        Initial Password for Local Auth Users
  --logging-level {debug,info,error}, -ll {debug,info,error}
                        Desired logging level

```

The following defaults for the command line arguments are in place:
* Default Config File Path is `./config/config.yaml`
  * Use the `-c` argument to specify a different path
* Default CSV File Path is `./data/userList.csv`
    * Use the `-f` argument to specify a different path
* Default Logging Level for the Console is set to INFO. 
  * Use the `-ll` argument to specify a different level
  * *Note:* Logging Level for the Log File (`./logs/app.log`) is set to DEBUG. This is not configurable via the command line.
* Default User Auth Type is `LOCAL` (Local Auth)
* Default Initial Password (for Local Auth Only) is `password123`


### Note regarding the user-auth-type command line argument

It is important to note that the `--user-auth-type` (`-t`) command line argument is important. This is used for *bulk adds/imports* of users only. It has no bearing on the export of users. 

The User Auth Type should be set to one of 3 values:
* `AD` - if adding a user from active directory
* `SAML` - if adding a user that will authenticate via SAML
* `LOCAL` - if adding a user that is purely local authentication
  * The Initial Password for these users will be set to the value of the `--user_initial_password` (`-p`) argument
  
## CSV FILE (INPUT/OUTPUT)

Both the import and the export mode require a CSV File Path to be provided. Here are the specifics on the CSV File Schema. 

### User List Export

The User List will export with the following headers:

* `email` - Should be the user's email address
* `full_name` - Should be set to the user's full name
* `username` - Should be set to the User's Username (for AD users do not include domain)
* `site_role` - Should be set to one of these values:
  * Creator 
  * Explorer 
  * ExplorerCanPublish 
  * SiteAdministratorExplorer 
  * SiteAdministratorCreator 
  * Unlicensed
  * Viewer

### User List Import (Add User Action)

The User List to import must contain the same CSV file headers as outlined above.

### Example CSV

```text
email,full_name,username,site_role
kmacpherson@tableau.com,Katie Macpherson,katiemacpherson,ServerAdministrator
rstryker@tableau.com,Ryan Stryker,ryanstryker,ServerAdministrator
```
## EXAMPLE - Exporting the User List for a Tableau Site

The command to execute a User List Export would look like:

```shell
python main.py -m export -f ./data/exportList.csv -ll debug
```
In the above command we are specifying that the logging level should be set to DEBUG.

In addition the *mode* `-m` of execution is set to 'export' and the file path to the CSV file containing
the user list is specified by the `-f` argument.

The configuration file is what defines which Tableau Server and Tableau Site to execute the action against. 

## EXAMPLE - Adding Users to a Tableau Site (AD)

The command to execute a User Add operation would look like:

```shell
python main.py -m import -t AD -f ./data/myListOfADUsers.csv -ll debug
```
In the above command we are specifying that the logging level should be set to DEBUG. 

In addition the *mode* `-m` of execution is set to 'import' and the file path to the CSV file containing
the import list is specified by the `-f` argument. 

The type of user auth is specified as `AD` via the `-t` argument, meaning we are importing AD Users.

Remember that the configuration file is what defines which Tableau Server and Tableau Site to execute the action against. 

## EXAMPLE - Adding Users to a Tableau Site (LOCAL)

The command to execute a User Add operation would look like:

```shell
python main.py -m import -t LOCAL -p changeme -f ./data/myListOfLocalUsers.csv -ll debug
```
In the above command we are specifying that the logging level should be set to DEBUG. 

In addition the *mode* `-m` of execution is set to 'import' and the file path to the CSV file containing
the import list is specified by the `-f` argument. 

The type of user auth is specified as `LOCAL` via the `-t` argument, meaning we are importing Local Auth Users.

The initial password for the imported users will be set to `changeme` as specified by the `-p` argument

Remember that the configuration file is what defines which Tableau Server and Tableau Site to execute the action against. 

## Authorship and Distribution

Developed by Tableau Professional Services. 

Please do not share or distribute this code beyond your organization. 

If you have any questions please contact Tableau Professional Services or your Tableau Sales team. 

----
Katie Macpherson - [kmacpherson@tableau.com](mailto:kmacpherson@tableau.com)


