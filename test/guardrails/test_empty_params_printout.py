import unittest
from azure_guardrails.shared import utils
from azure_guardrails.guardrails.policy_definition import Parameter, PolicyDefinition, Properties
from azure_guardrails.guardrails.services import Service, Services
import yaml
import ruamel.yaml
import json
import os

example_config_file = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "service-parameters-template.yml"
))


class EmptyParamsPrintoutTestCase(unittest.TestCase):
    def test_empty_params_printout(self):
        services = Service(service_name="Kubernetes")
        display_names = services.get_display_names_by_service_with_parameters(include_empty_defaults=True)
        expected_keys = [
            "Do not allow privileged containers in Kubernetes cluster",
            "Enforce internal load balancers in Kubernetes cluster",
            "Kubernetes cluster containers should not share host process ID or host IPC namespace",
            "Kubernetes cluster containers should only use allowed AppArmor profiles",
            "Kubernetes cluster containers should only use allowed ProcMountType",
            "Kubernetes cluster containers should only use allowed capabilities",
            "Kubernetes cluster containers should only use allowed seccomp profiles",
            "Kubernetes cluster containers should run with a read only root file system",
            "Kubernetes cluster pod FlexVolume volumes should only use allowed drivers",
            "Kubernetes cluster pod hostPath volumes should only use allowed host paths",
            "Kubernetes cluster pods and containers should only run with approved user and group IDs",
            "Kubernetes cluster pods and containers should only use allowed SELinux options",
            "Kubernetes cluster pods should only use allowed volume types",
            "Kubernetes clusters should be accessible only over HTTPS",
            "Kubernetes clusters should not allow container privilege escalation",
            "[Preview]: Kubernetes cluster services should only use allowed external IPs",
            "[Preview]: Kubernetes clusters should disable automounting API credentials",
            "[Preview]: Kubernetes clusters should not grant CAP_SYS_ADMIN security capabilities",
            "[Preview]: Kubernetes clusters should not use specific security capabilities",
            "[Preview]: Kubernetes clusters should not use the default namespace"
        ]
        keys = list(display_names.keys())
        keys.sort()
        # print(json.dumps(keys, indent=4))
        # Doing this in a loop to future-proof the unit test
        for expected_key in expected_keys:
            self.assertTrue(expected_key in keys)
        # print(ruamel.yaml.dump(display_names, Dumper=ruamel.yaml.RoundTripDumper))

        from jinja2 import Template, Environment, FileSystemLoader
        policies = {"Kubernetes": display_names}
        header_format_string = """# ---------------------------------------------------------------------------------------------------------------------
# {{ service_name }}
# ---------------------------------------------------------------------------------------------------------------------

{{ content }}
"""
        header_template = Template(header_format_string)
        service_entries = []
        for service_name, service_policies in policies.items():
            pretty_policies = ruamel.yaml.dump(service_policies, Dumper=ruamel.yaml.RoundTripDumper)
            rendered = header_template.render(dict(service_name=service_name, content=pretty_policies))
            service_entries.append(rendered)
        template_contents = dict(
            service_entries=service_entries,
        )
        template_path = os.path.join(os.path.dirname(__file__))
        env = Environment(loader=FileSystemLoader(template_path))  # nosec
        template = env.get_template("service-parameters-template.yml")
        result = template.render(t=template_contents)
        print(result)
