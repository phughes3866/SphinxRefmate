# pluginName should ideally match the top level directory name for the plugin
pluginEnv = {
    "pluginName":       "SphinxRefmate",
    "docsWeb":          "",
    "docsSublime":      "",
    "doDebug":          True
}
# pluginSettingsKey = {
#     "sphinx_check": {"default": True, "checks": ["is_bool"]},
#     "rst_check": {"default": True, "checks": ["is_bool"]},
#     "enable_context_menu": {"default": True, "checks": ["is_bool"]},
#     "priv_project_prefix": {"default": "priv", "checks": ["is_str"]},
#     "intersphinx_map_source_list": {"default": ["conf.py"], "checks": ["is_list_of_strings"]},
#     "bib_ref_file_list": {"default": ["index.rst"], "checks": ["is_list_of_strings"]},
#     "rst_epilog_source_list": {"default": ["conf.py"], "checks": ["is_list_of_strings"]},
#     "cur_proj_intersphinx_map_name": {"onlyProj": True, "default": "", "checks": ["is_str"]}
# }

pluginSettingsGovernor = {
    "ID": {
        "outputDictDesc": f"{pluginEnv['pluginName']} Plugin Settings"
    },
    "Settings": {
        "sphinx_check": {"default": True, "checks": ["is_bool"]},
        "rst_check": {"default": True, "checks": ["is_bool"]},
        "enable_context_menu": {"default": True, "checks": ["is_bool"]},
        "priv_project_prefix": {"default": "priv", "checks": ["is_str"]},
        "intersphinx_map_source_list": {"default": ["conf.py"], "checks": ["is_list_of_oom_strings"]},
        "bib_ref_file_list": {"default": ["index.rst"], "checks": ["is_list_of_oom_strings"]},
        "rst_epilog_source_list": {"default": ["conf.py"], "checks": ["is_list_of_oom_strings"]},
        "cur_proj_intersphinx_map_name": {"mergeDOnly": True, "default": "", "checks": ["is_str"]}
    }
}