import difflib
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


def dict_to_xml(name, data):
    """Convert nested dicts/lists to XML with flexible NODE/VALUE tags.
    Root MODULE uses `name` to set prefix, xmlns, and namespace.
    """
    def build_node(d, parent):
        if isinstance(d, dict):
            tag = d.get("tag", "NODE")
            attrib = {k: str(v) for k, v in d.items() if k != "tag" and not isinstance(v, (dict, list))}
            node = ET.SubElement(parent, tag, attrib)
            for v in d.values():
                if isinstance(v, (dict, list)):
                    build_node(v, node)
        elif isinstance(d, list):
            for item in d:
                build_node(item, parent)

    xmlns_value = f"http://{name}.com/{name}"
    root = ET.Element("MODULE", {
        "xmlns": xmlns_value,
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "https://github.com/alliedtelesis/apteryx-xml https://github.com/alliedtelesis/apteryx-xml/releases/download/v1.2/apteryx.xsd",
        "model": name,
        "namespace": xmlns_value,
        "prefix": name
    })

    build_node(data, root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode()


def normalize(xml):
    element = ET.fromstring(xml)
    rough_string = ET.tostring(element, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    return "\n".join(line for line in pretty.splitlines() if line.strip())


def assert_xml_equal(actual, expected):
    norm_actual = normalize(actual)
    norm_expected = normalize(expected)

    if norm_actual != norm_expected:
        diff = "\n".join(difflib.unified_diff(
            norm_expected.splitlines(),
            norm_actual.splitlines(),
            fromfile="expected",
            tofile="actual"
        ))
        raise AssertionError(f"XML mismatch:\n{diff}")


def pyang(yang, format="tree"):
    output = ""
    with tempfile.NamedTemporaryFile(dir="/tmp", delete=False, mode="w", suffix=".yang") as tmp_file:
        tmp_file.write(yang)
        tmp_file.flush()
        yang_file = tmp_file.name
        result = subprocess.run(
            ["pyang", "--plugindir", Path(__file__).resolve().parent.parent, "-f", format, str(yang_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pyang failed: {result.stderr}"
        output = result.stdout
    return output
