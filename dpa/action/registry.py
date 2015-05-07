
# ----------------------------------------------------------------------------
# Imports: 
# ----------------------------------------------------------------------------

from collections import defaultdict
from importlib import import_module
import logging as log
from os import path

import dpa
from dpa.config import Config
from dpa.ptask import PTaskArea
from dpa.singleton import Singleton

# ----------------------------------------------------------------------------
# Globals:
# ----------------------------------------------------------------------------

GLOBAL_ACTIONS_CONFIG = "config/actions/global.cfg"

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class ActionRegistry(Singleton):

    # ------------------------------------------------------------------------
    # Special methods:
    # ------------------------------------------------------------------------
    def init(self):
        self.reload_global_actions()
   
    # ------------------------------------------------------------------------
    # Instance methods:
    # ------------------------------------------------------------------------
    def get_action(self, action_name, target_type='none'):

        try:
            action = self._registered_actions[action_name][target_type]
        except KeyError:
            action = None

        return action

    # ------------------------------------------------------------------------
    def get_registered_actions(self, action_name=None):

        actions = []

        if action_name:
            action_dict = self._registered_actions
            for target_type in action_dict[action_name].keys():
                actions.append(action_dict[action_name][target_type])

        else:
            action_dict = self._registered_actions
            for action_name in action_dict.keys():
                for target_type in action_dict[action_name].keys():
                    actions.append(action_dict[action_name][target_type])

        return actions

    # ------------------------------------------------------------------------
    def load_global_actions(self):

        # get the global pipeline actions from the config files.
        action_config = PTaskArea.current().config(
            GLOBAL_ACTIONS_CONFIG,
            composite_ancestors=True,
        )

        for (target_type, actions) in action_config.items():
            for (action_name, settings) in actions.items():

                # try to import the module specified in the config.
                # then get the class from the imported module
                action_module_name = settings.get('module', None)
                action_class_name = settings.get('class', None) 
                doc = settings.get('help', "{t} {a} Action.".format(
                    t=target_type, a=action_name))
                try:
                    action_module = import_module(action_module_name)
                    action_class = getattr(action_module, action_class_name)
                except Exception as e:
                    log.error(str(e))
                    continue

                # if the action and target specified in the config matches
                # those in the action class itself, go ahead and register it.
                if (action_class.name == action_name and 
                    action_class.target_type == target_type):
                    self.register_action(action_class)

                # if not, then the config has overridden the action and/or 
                # target. We will create a dynamic subclass with the new 
                # specification which will allow for the creation of instances
                # with the new action/target. an optional docstring an be 
                # specified in the config as well.
                else:

                    # build a unique name for the subclass.
                    alias_subclass_name = \
                        target_type.title() + action_name.title() + \
                        action_class.__name__
                    
                    # create a dynamic subclass of the action with the new
                    # action name and/or target type
                    action_subclass = type(
                        alias_subclass_name,  # name of the subclass
                        (action_class,),      # base class tuple
                        {                     # class attributes to set
                            'name': action_name,
                            'target_type': target_type,
                            '__doc__': doc,
                        },
                    )

                    # now register the dynamic subclass
                    self.register_action(action_subclass)

    # ------------------------------------------------------------------------
    def reload_global_actions(self):

        self._registered_actions = defaultdict(dict)
        self._registered_targets = defaultdict(dict)
        self.load_global_actions()
                             
    # ------------------------------------------------------------------------
    def register_action(self, action_class, override=False):

        name = action_class.name
        target_type = action_class.target_type

        try:
            registered = self._registered_actions[name][target_type]
        except KeyError:
            # should fail if nothing is registered
            pass
        else:
            if not override:
                raise ActionRegistryError(
                    "Action '{n} {tn}' is already registered.".format(
                        n=name, tn=target_type
                    )
                )

        # register by action name and by target name
        self._registered_actions[name][target_type] = action_class
        self._registered_targets[target_type][name] = action_class

# ----------------------------------------------------------------------------
class ActionRegistryError(Exception):
    pass

