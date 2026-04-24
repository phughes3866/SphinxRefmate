from .lnk_parsingUtils import pluginSettingsManager

pluginSettingsSchema = {
    "rstEnvCheck"           :   {"profile"  :   "A",
                                 "default"  :   True,
                                 "checks"   :   ["is_bool"]
                                },
    "priv_project_prefix"   :   {"profile"  :   "A",
                                 "default"  :   "priv",
                                 "checks"   :   ["is_str"]
                                },
    "bib_ref_file_list"     :   {"profile"  :   "C",
                                 "default"  :   [],
                                 "checks"   :   ["is_list_of_zom_strings"]
                                },
    "intersphinx_self_key"  :   {"profile"  :   "B",
                                 "default"  :   "",
                                 "checks"   :   ["is_str"]
                                }
}

settingsControl = pluginSettingsManager(pluginSettingsSchema)
