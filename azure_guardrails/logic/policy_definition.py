import os
import logging
import json
from typing import Set, List, Optional

logger = logging.getLogger(__name__)


class PolicyDefinition:
    """
    PolicyDefinition Definition structure

    https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure
    """
    def __init__(self, policy_content: dict):
        self.content = policy_content
        self.id = policy_content.get("id")
        self.name = policy_content.get("name")
        self.display_name = policy_content.get("properties").get("displayName")
        self.category = policy_content.get("properties").get("metadata").get("category", None)
        self.properties = Properties(properties_json=policy_content.get("properties"))

    def __repr__(self):
        return json.dumps(self.content)

    def __str__(self):
        return json.dumps(self.content)

    @property
    def parameter_names(self) -> list:
        """Return the list of parameter names"""
        parameters = []
        for parameter in self.properties.parameters:
            parameters.append(parameter.name)
        return parameters

    @property
    def includes_parameters(self) -> bool:
        """Determine whether the policy supports parameters other than 'effect'"""
        result = False
        for parameter in self.parameter_names:
            if parameter == "effect":
                pass
            else:
                result = True
                break
        return result

    @property
    def allowed_effects(self) -> list:
        allowed_effects = []
        try:
            effect_parameter = self.properties.get_parameter_by_name("effect")
            allowed_effects = effect_parameter.allowed_values
        except AttributeError as error:
            # This just means that there is no effect in there.
            logger.debug(error)
            # Sometimes that is because deployIfNotExists or Modify is in the rule somewhere. Let's search it as a string
            if 'deployIfNotExists' in str(self.properties.policy_rule) and 'modify' in str(self.properties.policy_rule):
                logger.debug(f"Found BOTH deployIfNotExists and modify in the policy content for the policy: {self.display_name}")
                allowed_effects.append("deployIfNotExists")
                allowed_effects.append("modify")
            elif 'deployIfNotExists' in str(self.properties.policy_rule):
                logger.debug(f"Found deployIfNotExists in the policy content for the policy: {self.display_name}")
                allowed_effects.append("deployIfNotExists")
            elif 'modify' in str(self.properties.policy_rule):
                logger.debug(f"Found Modify in the policy content for the policy: {self.display_name}")
                allowed_effects.append("modify")
            else:
                logger.debug(error)

        if allowed_effects:
            # TODO: Determine if the effect is supposed to be case sensitive
            lowercase_allowed_effects = [x.lower() for x in allowed_effects]
            return lowercase_allowed_effects
        else:
            return []

    @property
    def modifies_resources(self) -> bool:
        # Effects: https://docs.microsoft.com/en-us/azure/governance/policy/concepts/effects
        if "append" in self.allowed_effects or "modify" in self.allowed_effects:
            return True
        else:
            return False


class Parameter:
    """
    Parameter properties

    https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure#parameter-properties
    """
    def __init__(self, name, parameter_json):
        self.name = name
        self.parameter_json = parameter_json
        self.type = self.parameter_json.get("type")
        self.default_value = self.parameter_json.get("defaultValue", None)
        self.allowed_values = self.parameter_json.get("allowedValues", None)

        # Metadata
        self.metadata_json = parameter_json.get("metadata")
        self.description = self.metadata_json.get("description")
        self.display_name = self.metadata_json.get("displayName")
        self.category = self.metadata_json.get("category", None)
        self.strong_type = self.metadata_json.get("strongType", None)
        self.assign_permissions = self.metadata_json.get("assignPermissions", None)

    def _allowed_values(self):
        allowed_values = self.parameter_json.get("allowedValues", None)
        allowed_values = [x.lower() for x in allowed_values]
        return allowed_values


class Properties:
    def __init__(self, properties_json: dict):
        self.properties_json = properties_json
        # Values
        self.display_name = properties_json.get("displayName")
        self.policy_type = properties_json.get("policyType")
        self.mode = properties_json.get("mode")
        self.description = properties_json.get("description")

        # Metadata
        self.metadata_json = properties_json.get("metadata")
        self.version = self.metadata_json.get("version", None)
        self.category = self.metadata_json.get("category", None)
        self.preview = self.metadata_json.get("preview", None)
        self.deprecated = self.metadata_json.get("deprecated", None)

        # PolicyDefinition Rule and Parameters
        self.policy_rule = properties_json.get("policyRule")
        self.parameters = self._parameters()

    def __repr__(self):
        return self.properties_json

    def _parameters(self) -> List[Optional[Parameter]]:
        parameters = []
        parameter_json = self.properties_json.get("parameters")
        if parameter_json:
            for name, value in self.properties_json.get("parameters").items():
                parameter = Parameter(name=name, parameter_json=value)
                parameters.append(parameter)
        return parameters

    def parameter_name_exists(self, parameter_name) -> bool:
        try:
            parameter_json = self.properties_json.get("parameters").get(parameter_name)
            if parameter_json:
                return True
            else:
                return False
        except:
            return False

    def get_parameter_by_name(self, parameter_name) -> Parameter:
        try:
            parameter_json = self.properties_json.get("parameters").get(parameter_name)
            if parameter_json:
                parameter = Parameter(name=parameter_name, parameter_json=parameter_json)
                return parameter
        except:
            logger.debug("No parameter found with the name %s" % parameter_name)
