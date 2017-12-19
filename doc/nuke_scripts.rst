..
    :copyright: Copyright (c) 2015 ftrack

############
Nuke scripts
############

Publishing and versioning a script
==================================

Scripts can be published and versioned up directly from the File menu in Nuke.
Follow these steps to version control a script:

1. Save it with _v# in the filename. Example: scriptname_v1.nk.
2. Select :menuselection:`Publish script...` from the File menu and select a
   task you want to associate this script with.

When you want to version up, select :menuselection:`Publish script` to a new
version to increment the name of the script and publish it to ftrack.

.. note::

    To publish nuke scripts, you currently must have an asset type with code
    `comp`. An error with the message *Asset type not valid* will appear
    otherwise. You can configure asset types from System settings in ftrack. 

Opening a published script
==========================

Nuke scripts that are published to ftrack can be opened directly from the File
menu.

1. Select :menuselection:`Open published script...`
2. Browse to a shot and select a script to open it. Nuke scripts exported from
   HIERO can be opened from this menu to quickly start working.
