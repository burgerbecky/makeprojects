Functions
=========

Dispatchers
^^^^^^^^^^^
.. doxygenfunction:: makeprojects::build
.. doxygenfunction:: makeprojects::clean
.. doxygenfunction:: makeprojects::rebuild

Configuration
^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::config::savedefault
.. doxygenfunction:: makeprojects::config::find_default_build_rules
.. doxygenfunction:: makeprojects::config::import_configuration

Clean
^^^^^
.. doxygenfunction:: makeprojects::cleanme::dispatch
.. doxygenfunction:: makeprojects::cleanme::process
.. doxygenfunction:: makeprojects::cleanme::main

Build
^^^^^
.. doxygenfunction:: makeprojects::buildme::build_rez_script
.. doxygenfunction:: makeprojects::buildme::build_slicer_script
.. doxygenfunction:: makeprojects::buildme::build_doxygen
.. doxygenfunction:: makeprojects::buildme::build_watcom_makefile
.. doxygenfunction:: makeprojects::buildme::build_makefile
.. doxygenfunction:: makeprojects::buildme::parse_sln_file
.. doxygenfunction:: makeprojects::buildme::build_visual_studio
.. doxygenfunction:: makeprojects::buildme::parse_mcp_file
.. doxygenfunction:: makeprojects::buildme::build_codewarrior
.. doxygenfunction:: makeprojects::buildme::parse_xcodeproj_dir
.. doxygenfunction:: makeprojects::buildme::build_xcode
.. doxygenfunction:: makeprojects::buildme::parse_codeblocks_file
.. doxygenfunction:: makeprojects::buildme::build_codeblocks
.. doxygenfunction:: makeprojects::buildme::main

Rebuild
^^^^^^^
.. doxygenfunction:: makeprojects::rebuildme::main
