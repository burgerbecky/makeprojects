# 🐍 Build Rules

Makeprojects is controlled by a configuration file called ``build_rules.py``. It's a python script with global variables and functions that will control how ``buildme``, ``cleanme``, ``rebuildme``, and ``makeprojects`` behave. Since it's a python script, there is no limit to what the script can do to perform any build or clean operation for any project.

When a directory is checked for processing, a ``build_rules.py`` file is checked. If it doesn't exist, the parent directory is checked until the root directory is found which stops the scanning. If the file is not found, processing will stop. If found, it will be checked if it is in the folder being processed and is used if so. If the file is in a parent folder, a ``GENERIC_*`` variable is checked to see if the ``build_rules.py`` qualifies as a "catch all" file that handles rules for all child folders.

Below, are the functions and variables that the ``build_rule.py`` may or may not contain to control the tool's behavior. If the value is it not found, the defaults are shown below.

*Note:* ``rebuildme`` performs a ``cleanme`` and then a ``buildme`` operation, so it processes both ``CLEANME_*`` and ``BUILDME_*`` parameters.

## 🧹 Cleanme rules

``cleanme`` and ``rebuildme`` check for several global variables and the existence of a single function that will perform cleaning operations.

Full documentation on the operation of [cleanme is here](cleanme_man.md).

### CLEANME_GENERIC

``` python
# ``cleanme`` will process any child directory with the clean() function if
# True.
CLEANME_GENERIC = False
```

If set to ``True``, ``cleanme`` and ``rebuildme`` will assume this ``build_rules.py`` file is designed to be generic and if invoked from a child directory, it will be given the child's directory for processing. If ``False`` it will only be invoked with the directory that the build_rules files resides in. This is needed to prevent a ``build_rules.py`` file from processing directories that it was not meant to handle when parent directory traversal is active. If this does not exist, the default of ``False`` is used.

### CLEANME_CONTINUE

``` python
# ``cleanme`` will process build_rules.py in the parent folder if True.
CLEANME_CONTINUE = False
```

If set to ``True``, ``cleanme`` and ``rebuildme`` will process this file and then traverse the parent directory looking for another ``build_rules.py`` file to continue the ``cleanme`` operation. This is useful when there's a generic clean operation in a root folder and this function performs custom operations unknown to the parent rules file. If this doesn't exist, the default of ``False`` is assumed.

### CLEANME_DEPENDENCIES

``` python
# ``cleanme`` will clean the listed folders using their rules before cleaning.
# this folder.
CLEANME_DEPENDENCIES = []
```

``cleanme`` and ``rebuildme`` will clean the listed folders using their rules before cleaning this folder. Only folders are allowed, files generate an error. If this doesn't exist, the default of an empty list is assumed.

### CLEANME_NO_RECURSE

``` python
# If set to True, ``cleanme -r``` will not parse directories in this folder.
CLEANME_NO_RECURSE = False
```

If set to ``True``, ``cleanme -r`` and ``rebuildme -r`` will not parse directories in this folder. If this does not exist, the default of ``False`` is used. The main purpose of this is to prevent scanning child folders when it is already known that there are no child folders that need processing or that ``CLEANME_DEPENDENCIES`` lists every child folder of interest, so recursion is not necessary.

### CLEANME_PROCESS_PROJECT_FILES

``` python
# ``cleanme`` will assume only the function ``clean()`` is used if True.
CLEANME_PROCESS_PROJECT_FILES = False
```

If set to ``False``, ``cleanme`` will disable scanning for project files and assume that the function ``clean()`` in build_rules.py performs all actions to clean the directory. If this doesn't exist, the default of ``False`` is assumed. Set this to ``True`` if the ``clean()`` function performs all of the operations needed to remove temporary files without the need to invoke any IDE.

### clean(working_directory)

``` python
def clean(working_directory):
    return None
```

This function should delete all temporary files that were created after a project is built. In most cases, IDEs will be able to handle this, but for some projects, there are other files such as headers or compiled shaders that the IDE is not aware of. This function will perform the deletion functions and return either 0 for no error, or non-zero for an error that will be reported once ``cleanme`` is finished processing.

If the variable ``CLEANME_GENERIC`` is ``False``, the working_directory is guaranteed to only be the directory that the ``build_rules.py`` resides in. If ``CLEANME_GENERIC`` is ``False`` then the directory could be any of the child folders the ``build_rules.py`` file resides in.

Returning ``None`` alerts ``cleanme`` and ``rebuildme`` that this function is not implemented and no action was performed.

## 👷 Buildme rules

``buildme`` and ``rebuildme`` checks for several global variables and the existence of three functions that will perform building operations.

Full documentation on the operation of [buildme is here](buildme_man.md).

### BUILDME_GENERIC

``` python
# Process any child directory with the prebuild(), build(), and postbuild()
# functions if True.
BUILDME_GENERIC = False
```

If set to ``True``, ``buildme`` will assume this ``build_rules.py`` file is designed to be generic and if invoked from a child directory, it will be given the child's directory for processing. If ``False`` it will only be invoked with the directory that the ``build_rules.py`` files resides in. This is needed to prevent a ``build_rules.py`` file from processing directories that it was not meant to handle when parent directory traversal is active. If this does not exist, the default of ``False`` is used.

### BUILDME_CONTINUE

``` python
# ``buildme`` will process build_rules.py in the parent folder if True.
BUILDME_CONTINUE = False
```

If set to ``True``, ``buildme`` and ``rebuildme`` will process this file and then traverse the parent directory looking for another ``build_rules.py`` file to continue the ``buildme`` operation. This is useful when there's a generic build operation in a root folder and this function performs custom operations unknown to the parent rules file. If this doesn't exist, the default of ``False`` is assumed.

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

### BUILDME_PROCESS_PROJECT_FILES

``` python
# ``buildme`` will assume only the three functions are used if True.
BUILDME_PROCESS_PROJECT_FILES = True
```

If set to ``False``, ``buildme`` will disable scanning for project files and assume that the functions ``prebuild()``, ``build()``, and ``postbuild()`` in build_rules.py perform all the actions to build the files in this directory. If this doesn't exist, the default of ``True`` is assumed.

### prebuild(working_directory, configuration)

``` python
def prebuild(working_directory, configuration)
    return None
```

If this optional function exists, it will be called **FIRST** with the directory requested to build and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules. If ``BUILDME_GENERIC`` is ``False``, only the directory that the ``build_rules.py`` file resides in will be passed as the ``working_directory``.

This function will perform build functions and return either 0 for no error, or non-zero for an error that will be reported once ``buildme`` is finished processing. Return ``None`` if this function does no operation.

### build(working_directory, configuration)

``` python
def build(working_directory, configuration)
    return None
```

If this optional function exists, it will be called after ``prebuild()`` is called but before any other the IDE project files are processed. It will passed the directory requested to build and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules. If ``BUILDME_GENERIC`` is ``False``, only the directory that the ``build_rules.py`` file resides in will be passed as the ``working_directory``.

This function will perform build functions and return either 0 for no error, or non-zero for an error that will be reported once ``buildme`` is finished processing. Return ``None`` if this function does no operation.

### postbuild(working_directory, configuration)

``` python
def postbuild(working_directory, configuration)
    return None
```

If this optional function exists, it will be called **LAST** with the directory requested to build and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules. If ``BUILDME_GENERIC`` is ``False``, only the directory that the ``build_rules.py`` file resides in will be passed as the ``working_directory``.

This function will perform build functions and return either 0 for no error, or non-zero for an error that will be reported once ``buildme`` is finished processing. Return ``None`` if this function does no operation.

## 👩‍🍳 Makeprojects rules

### DEFAULT_PROJECT_NAME

``` python
# Default project name to use instead of the name of the working directory
# DEFAULT_PROJECT_NAME = os.path.basename(working_directory)
```

When ``makeprojects`` is invoked, if a project name is not specified, this variable will declare the default project name. The default is the name of the folder that is being processed.

## 👩‍🔧 Main

``` python
# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(build(os.path.dirname(os.path.abspath(__file__)), 'all'))
```

The ``build_rules.py`` file can be run as a standalone script. If the line above exists in the script, it will call whatever function is declared and exit to the operating system. The example above will call the ``build()`` function with the current directory, however, it's up to the programmer to decide what is the default action and if parameters should be passed and what to do with them.
