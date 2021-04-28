===================================
Project Templates
===================================
This module does not inherit or modify the project.project model. Therefore, if you decide to uninstall it, the projects created with this wizard will not be affected.

Instalation
===========

-  Unzip all these modules next to eachother in your custom addons
   folder.
-  Restart your Odoo instance.
-  Install ``project_from_template``.

Upgrading to a newer version
============================

-  Unzip all new modules and replace the existing ones.
-  Run ``./odoo-bin -d YOUR_DB_NAME -u project_from_template``
-  Restart the Odoo instance.

Usege
============================

-  With the project manager permissions. Go to Settings -> Project Templates
-  Create your template: set project stages, create project tasks, if you want, you can set the parameters to auto calculate the due date of each task based on the project start date or the previous task due date.
-  When you're done editing your project template, enable it so they can be chosen from the project creation wizard.
-  To create a new project from a template, press the new button << Create from template >> next to the Create button in the main Kanban view of the projects. Select an enabled template and change the values as you see fit. If there are tasks with the calculated deadline, you must set the project start date necessarily.


Release logs
------------

* v13.0.0.2

   *  small bug fixed that occurred when loading a template without stages.

* v13.0.0.1

   *  [Feature] Initial version of the source code: Create Projects from templates