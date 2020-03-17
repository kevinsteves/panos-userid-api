PAN-OS User-ID API
==================

The PAN-OS User-ID API can be used to update dynamic objects on PAN-OS
firewalls and Panorama.  Dynamic objects do not require a
configuration commit, and include:

 =================   ================================
 Object              Mapping
 =================   ================================
 ip-user             User to IP
 groups              User to Group
 registered-ip       Tag to IP (host, network, range)
 registered-user     Tag to User (for User Groups)
 =================   ================================

The ``type=user-id`` PAN-OS XML API request is used with a
**uid-message** XML document which specifies the type of update and
the data to update.  Update types include:

 =================   ================================
 Object              Update Types
 =================   ================================
 ip-user             login, logout
 groups              groups
 registered-ip       register, unregister
 registered-user     register-user, unregister-user
 =================   ================================

`Documentation
<http://api-lab.paloaltonetworks.com/module-3.html>`_
including **uid-message** formats, examples and labs is
available.

userid-api.py
-------------

 ``userid-api.py`` is a Python3 command line program that can
 be used to perform testing of the User-ID API including:

 - function
 - performance
 - capacity

 ``userid-api.py`` uses the
 `pan.xapi
 <https://github.com/kevinsteves/pan-python/blob/master/doc/pan.xapi.rst>`_
 module in
 `pan-python
 <https://github.com/kevinsteves/pan-python>`_
 to perform PAN-OS XML API requests.

Usage
~~~~~

 ::

    $ userid-api.py -h
    usage: userid-api.py [options]

    optional arguments:
      -h, --help            show this help message and exit
      -t T                  .panrc tagname
      -n N                  number of ip mappings
      --net NET             starting network (default: 10.0.0.0/8)
      --chunk CHUNK         chunk size (default: 1024)
      --timeout TIMEOUT     ip-user timeout in minutes (default: None)
      --login               login users (ip-user)
      --logout              logout users
      --register            register tags (registered-ip)
      --unregister          unregister tags
      --persistent {0,1}    registered-ip persistent attribute (default: None)
      --tags TAGS [TAGS ...]
                            registered-ip tags (default: tag01 tag02)
      --print               print XML uid-message documents only

Example
~~~~~~~

 ::

    $ userid-api.py -t vm-50 --register -n 1000
    elapsed 3.41 chunk 1024 num 1000
    292.97 registers/sec

    admin@PA-VM-50> show object registered-ip all option count


    Total: 1000 registered addresses

    $ userid-api.py -t vm-50 --unregister -n 1000
    elapsed 0.44 chunk 1024 num 1000
    2273.66 unregisters/sec

    admin@PA-VM-50> show object registered-ip all option count


    Total: 0 registered addresses
