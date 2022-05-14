# 👀 Build Rules

Makeprojects is controlled by a configuration file called ``build_rules.py``. It's a python script with global variables and functions that will control how ``buildme``, ``cleanme``, ``rebuildme``, and ``makeprojects`` behaves. Since it's a python script, there is no limit to what the script can do to perform any build or clean operation for any project.

When a directory is checked for processing, a ``build_rules.py`` file is checked. If it doesn't exist, the parent directory is checked until the root directory is found which stops the scanning. If the file is not found, processing will stop. If found, it will be checked if it is in the folder being processed and is used if so. If the file is in a parent folder, a ``GENERIC_*`` variable is checked to see if the ``build_rules.py`` qualifies as a "catch all" file that handles rules for all child folders.

Below, are the functions and variables that the ``build_rule.py`` may or may not contain to control the tool's behavior. If the value is it not found, the defaults are shown below.

## 🧹 Cleanme rules

``cleanme`` checks for several global variables and the existence of a single function that will perform cleaning operations.

### CLEANME_GENERIC

``` python
# ``cleanme`` will process any child directory with the clean() function if
# True.
CLEANME_GENERIC = False
```

If set to ``True``, ``cleanme`` will assume this build_rules file is designed to be generic and if invoked from a child directory, it will be given the child's directory for processing. If ``False`` it will only be invoked with the directory that the build_rules files resides in. This is needed to prevent a build_rules file from processing directories that it was not meant to handle when parent directory traversal is active. If this does not exist, the default of ``False`` is used.

### CLEANME_CONTINUE

``` python
# ``cleanme`` will process build_rules.py in the parent folder if True.
CLEANME_CONTINUE = False
```

If set to ``True``, ``cleanme`` will process this file and then traverse the parent directory looking for another ``build_rules.py`` to continue the ``cleanme`` operation. This is useful when there's a generic clean operation in a root folder and this function performs custom operations unknown to the parent rules file. If this doesn't exist, the default of ``False`` is assumed.

### CLEANME_DEPENDENCIES

``` python
# ``cleanme`` will clean the listed folders using their rules before cleaning.
# this folder.
CLEANME_DEPENDENCIES = []
```

``cleanme`` will clean the listed folders using their rules before cleaning this folder. Only folders are allowed, files generate an error. If this doesn't exist, the default of an empty list is assumed.

### CLEANME_NO_RECURSE

``` python
# If set to True, ``cleanme -r``` will not parse directories in this folder.
CLEANME_NO_RECURSE = False
```

If set to ``True``, "cleanme -r" will not parse directories in this folder. If this does not exist, the default of ``False`` is used.

### CLEANME_PROCESS_PROJECT_FILES

``` python
# ``cleanme`` will assume only the function ``clean()`` is used if True.
CLEANME_PROCESS_PROJECT_FILES = False
```

If set to ``False``, ``cleanme`` will disable scanning for project files and assume that the function ``clean()`` in build_rules.py performs all actions to clean the directory. If this doesn't exist, the default of ``False`` is assumed.

### clean(working_directory)

``` python
def clean(working_directory):
    return None
```

This function will delete all temporary files that were created after a project is built. In most cases, IDEs will be able to handle this, but for some project, there are other files such as headers or compiled shaders that the IDE is not aware of. This function will perform the deletion functions and return either 0 for no error, or non-zero for an error that will be reported once ``cleanme`` is finished processing.

If the variable ``CLEANME_GENERIC`` is ``False``, the working_directory is guaranteed to only be the directory that the ``build_rules.py`` resides in. If ``CLEANME_GENERIC`` is ``False`` then the directory could be any of the child folders the ``build_rules.py`` file resides in.

Returning ``None`` alerts ``cleanme`` that this function is not implemented and no action was performed.

## 👷 Buildme rules

``buildme`` checks for several global variables and the existence of a single function that will perform building operations.

### BUILDME_GENERIC

``` python
# Process any child directory with the prebuild(), build(), and postbuild()
# functions if True.
BUILDME_GENERIC = False
```

If set to ``True``, ``buildme`` will assume this build_rules file is designed to be generic and if invoked from a child directory, it will be given the child's directory for processing. If ``False`` it will only be invoked with the directory that the build_rules files resides in. This is needed to prevent a build_rules file from processing directories that it was not meant to handle when parent directory traversal is active. If this does not exist, the default of ``False`` is used.

### BUILDME_DEPENDENCIES

``` python
# Build the folders listed before processing this folder.
BUILDME_DEPENDENCIES = []
```

Set ``BUILDME_DEPENDENCIES`` with a list of folders or project files that must be built first. They will be built in the order they appear in this list. The default is no dependencies.

### BUILDME_NO_RECURSE

``` python
# Disable recursion in all directories found in this directory.
BUILDME_NO_RECURSE = True
```

Set ``BUILDME_NO_RECURSE`` to True if all subdirectories below this folder are not to be processed due to them not having any build project files. This defaults to ``False``, but set this to ``True`` to prevent parsing folders that don't need processing.

### prebuild(working_directory, configuration)

If this function exists, it will be called **FIRST** with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.

### build(working_directory, configuration)

If this function exists, it will be called with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.

### postbuild(working_directory, configuration)

If this function exists, it will be called **LAST** with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.