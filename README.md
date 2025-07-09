# PyOS Developer Preview 0.1.3



This Is A VERY Janky PyOs (Python-OS) That runs fully under python

It Has A Realistic-ish Boot Process With A kernel Init and A login Prompt

 
# Working:

  * pkg (package manager)
  * service(service manager)
  * ls/rm/cp/mv/cat/touch/reboot(only reboot -s works)/
  * ps(only ps windows only works for now)/kill (windows PIDS ONLY)/free (System Ram)/du/df
  * removing/ adding users
  * Edit (VERY JANKY)


# Being Worked On:


  * proper services (graphics, sound, ethernet(kinda works)
  * GUI
  * TTY Like Terminal
  * Good Packages
  * Error Management
  * Way More Commands


# Todo:
  
  * Full Os
  * Linux/MacOS Support
  * AutoInstall Dependencies for python
  * Apps For Gui
  * Loading programs into Ram/Environ for access anywhere
  * Pkg Working Outside of Local Ips (Only works on 192.168.0.150 at port 5000 i think)
  * OOBE/ First Boot Setup
  * A good file editor
  * A Service Closer

# Disclamer:
  * THIS ONLY WORKS ON WINDOWS (tested on windows 11)
  * THIS ALSO ONLY HAS BEEN TESTED ON PYTHON 3.10-3.12(i think)
  * I DONT KNOW THE DEPENDENCIES THAT ARE NEEDED(sorry)

# How To Run:
```
  cd into the root of the image (where bin,boot,etc,etc...)
  then run python boot/boot.py
```
  * 2 USERS:
    * ROOT : ROOT
    * USER : USER

# How To Make Packages:
  * FIRST: 
    * TO INSTALL LOCAL PACKAGES PLEASE INSTALL .ZIP FILES IN THE REPO FOLDER IN THE ROOT
  * In The Shell Run:
```
    pkg install cpkroot
    pkg install build
```
  * Then To Make A Package Run:
```
    cpkroot [PKG NAME]
    cd [PKG_NAME]
    edit exec.py*
    cd ..
    build [PKG_NAME]
```
  * Exec.py looks like this:
```
    def frun():
      ...

    def main(args):
      ...
```
  * What To Change
      * Frun:
        * This Gets Ran When Installed.
      * Main:
        * This Gets Ran Every Time Shell Runs It
      * How To Configure Packages
        ```
          import service_api
          def frun():
            service_api.register_service('[NAME]')
        ```
        * This Will Make A New Service
        * The Service Path HAS TO BE [PKG_PATH]/daemon.py
        * Please Make Keyboard Interupt bypass
        * And Now You Can Write ANYTHING In It
        * There Is No Definition Needed.
# Changing Kernel Code
* If You Want To Change The Kernel Code, The Current Code Is In The kernel folder
* install the buildkrnl package
* then at the root, run buildkrnl

      
