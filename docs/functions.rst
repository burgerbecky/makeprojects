Functions
=========

Dispatchers
-----------

makeprojects.build
^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::build

makeprojects.clean
^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::clean

makeprojects.rebuild
^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::rebuild

Generators
----------

makeprojects.new_solution
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::new_solution

makeprojects.new_project
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::new_project

makeprojects.new_configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::new_configuration

Configuration
-------------

config.save_default
^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::config::save_default

config.find_default_build_rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::config::find_default_build_rules

Clean
-----

cleanme.dispatch
^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::cleanme::dispatch

cleanme.process
^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::cleanme::process

cleanme.main
^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::cleanme::main

Build
-----

buildme.build_rez_script
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_rez_script

buildme.build_slicer_script
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_slicer_script

buildme.build_doxygen
^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_doxygen

buildme.build_makefile
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_makefile

buildme.parse_sln_file
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::parse_sln_file

buildme.parse_mcp_file
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::parse_mcp_file

buildme.build_codewarrior
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_codewarrior

buildme.parse_xcodeproj_file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::parse_xcodeproj_file

buildme.build_xcode
^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_xcode

buildme.parse_codeblocks_file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::parse_codeblocks_file

buildme.build_codeblocks
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::build_codeblocks

buildme.add_build_rules
^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::add_build_rules

buildme.add_project
^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::add_project

buildme.get_projects
^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::get_projects

buildme.process
^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::process

buildme.main
^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::buildme::main

Rebuild
-------

rebuild.main
^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::rebuildme::main

Enums
-----

enums.source_file_filter
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::enums::source_file_filter

enums.get_installed_visual_studio
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::enums::get_installed_visual_studio

enums.get_installed_xcode
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::enums::get_installed_xcode

enums.platformtype_short_code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::enums::platformtype_short_code

enums.get_output_template
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::enums::get_output_template

Util
----

util.validate_enum_type
^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::validate_enum_type

util.regex_dict
^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::regex_dict

util.validate_boolean
^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::validate_boolean

util.validate_string
^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::validate_string

util.clear_build_rules_cache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::clear_build_rules_cache

util.load_build_rules
^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::load_build_rules

util.getattr_build_rules
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::getattr_build_rules

util.getattr_build_rules_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::getattr_build_rules_list

util.add_build_rules
^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::add_build_rules

util.get_build_rules
^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::get_build_rules

util.remove_ending_os_sep
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::remove_ending_os_sep

util.was_processed
^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::was_processed

util.fixup_args
^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::fixup_args

util.convert_file_name
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::convert_file_name

util.do_generate_build_rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::do_generate_build_rules

util.iterate_configurations
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::util::iterate_configurations

validators.lookup_enum_value
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_enum_value

validators.lookup_enum_append_key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_enum_append_key

validators.lookup_enum_append_keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_enum_append_keys

validators.lookup_strings
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_strings

validators.lookup_string_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_string_list

validators.lookup_string_lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_string_lists

validators.lookup_booleans
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::validators::lookup_booleans

Defaults
--------

defaults.settings_from_name
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::settings_from_name

defaults.configuration_presets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::configuration_presets

defaults.get_project_name
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::get_project_name

defaults.get_project_type
^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::get_project_type

defaults.get_platform
^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::get_platform

defaults.guess_ide
^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::guess_ide

defaults.get_ide
^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::get_ide

defaults.default_configuration_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::default_configuration_list

defaults.get_configuration_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::defaults::get_configuration_list

Visual Studio
-------------

visual_studio.SUPPORTED_IDES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenvariable:: makeprojects::visual_studio::SUPPORTED_IDES

visual_studio.parse_sln_file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::parse_sln_file

visual_studio.match
^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::match

visual_studio.create_build_object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::create_build_object

visual_studio.create_clean_object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::create_clean_object

visual_studio.test
^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::test

visual_studio.get_uuid
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::get_uuid

visual_studio.create_copy_file_script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::create_copy_file_script

visual_studio.create_deploy_script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::create_deploy_script

visual_studio.do_filter_tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::do_filter_tree

visual_studio.generate
^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio::generate

visual_studio_utils.get_path_property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::get_path_property

visual_studio_utils.get_toolset_version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::get_toolset_version

visual_studio_utils.convert_file_name_vs2010
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::convert_file_name_vs2010

visual_studio_utils.wiiu_props
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::wiiu_props

visual_studio_utils.add_masm_support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::add_masm_support

visual_studio_utils.get_cpu_folder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::get_cpu_folder

visual_studio_utils.generate_solution_file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::visual_studio_utils::generate_solution_file

Watcom
------

watcom.SUPPORTED_IDES
^^^^^^^^^^^^^^^^^^^^^
.. doxygenvariable:: makeprojects::watcom::SUPPORTED_IDES

watcom.match
^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom::match

watcom.create_build_object
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom::create_build_object

watcom.create_clean_object
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom::create_clean_object

watcom.test
^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom::test

watcom.generate
^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom::generate

watcom_util.fixup_env
^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::fixup_env

watcom_util.convert_file_name_watcom
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::convert_file_name_watcom

watcom_util.get_element_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::get_element_dict

watcom_util.get_custom_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::get_custom_list

watcom_util.get_output_list
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::get_output_list

watcom_util.get_obj_list
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::get_obj_list

watcom_util.add_obj_list
^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::add_obj_list

watcom_util.add_post_build
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::add_post_build

watcom_util.watcom_linker_system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::watcom_linker_system

watcom_util.warn_if_invalid
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. doxygenfunction:: makeprojects::watcom_util::warn_if_invalid
