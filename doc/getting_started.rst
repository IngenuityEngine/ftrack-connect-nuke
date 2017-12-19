..
    :copyright: Copyright (c) 2016 ftrack

.. _getting_started:

***************
Getting started
***************

To get started with the Nuke integration, follow the instructions below.

1.  Install `ftrack connect <https://ftrack.com/connect>`_ (the package comes
    bundled with various integrations). 
2.  Launch and sign in to ftrack connect.
3.  Launch the Nuke action. Either by pressing the actions icon on a task in the
    web UI, or by first selecting a task in the Connect interface.
4.  Select ftrack as the asset manager in Nuke. Open
    "Asset manager -> Preferences", select ftrack as Manager and press Apply.

.. image:: /image/getting_started-select_asset_maganger.png

5.  The integration currently depends on a few asset types being present in
    ftrack. From System Settings -> Workflow -> Asset types, make sure the asset
    types with the following codes are available:

    * `comp`
    * `img`
    * `render`
    * `nuke_gizmo`
