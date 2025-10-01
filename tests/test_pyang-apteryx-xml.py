import pytest
from conftest import assert_xml_equal, dict_to_xml, pyang
from yang import Leaf, Module, Typedef


def test_tree_basic_format():
    yang = """
    module example {
        namespace "http://example.com/example";
        prefix ex;
        container test-container {
            leaf test-leaf {
                type string;
            }
        }
    }
    """
    print(yang)
    output = pyang(yang, format="tree")
    expected_lines = [
        "module: example",
        "  +--rw test-container",
        "     +--rw test-leaf?   string"
    ]
    for line in expected_lines:
        assert line in output, f"Expected line not found: {line}"


def test_xml_basic_format():
    yang = """
    module example {
        namespace "http://example.com/example";
        prefix ex;
        container test-container {
            leaf test-leaf {
                type string;
            }
        }
    }
    """
    print(yang)
    expected = """<?xml version='1.0' encoding='UTF-8'?>
    <MODULE xmlns="http://example.com/example" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://github.com/alliedtelesis/apteryx-xml https://github.com/alliedtelesis/apteryx-xml/releases/download/v1.2/apteryx.xsd" model="example" namespace="http://example.com/example" prefix="ex">
        <NODE name="test-container">
            <NODE name="test-leaf" mode="rw"/>
        </NODE>
    </MODULE>
    """
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_string():
    yang = Module("example", children=[Leaf("test", "string")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_boolean():
    yang = Module("example", children=[Leaf("test", "boolean")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "children": [{"tag": "VALUE", "name": "true", "value": "true"}, {"tag": "VALUE", "name": "false", "value": "false"}]}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def run_range(type, range):
    yang = Module("example", children=[Leaf("test", type)]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "range": range}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_int8():
    run_range("int8", "-128..127")


def test_xml_int16():
    run_range("int16", "-32768..32767")


def test_xml_int32():
    run_range("int32", "-2147483648..2147483647")


def test_xml_int64():
    yang = Module("example", children=[Leaf("test", "int64")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "(-([0-9]{1,18}|[1-8][0-9]{18}|9([01][0-9]{17}|2([01][0-9]{16}|2([0-2][0-9]{15}|3([0-2][0-9]{14}|3([0-6][0-9]{13}|7([01][0-9]{12}|20([0-2][0-9]{10}|3([0-5][0-9]{9}|6([0-7][0-9]{8}|8([0-4][0-9]{7}|5([0-3][0-9]{6}|4([0-6][0-9]{5}|7([0-6][0-9]{4}|7([0-4][0-9]{3}|5([0-7][0-9]{2}|80[0-8]))))))))))))))))|([0-9]{1,18}|[1-8][0-9]{18}|9([01][0-9]{17}|2([01][0-9]{16}|2([0-2][0-9]{15}|3([0-2][0-9]{14}|3([0-6][0-9]{13}|7([01][0-9]{12}|20([0-2][0-9]{10}|3([0-5][0-9]{9}|6([0-7][0-9]{8}|8([0-4][0-9]{7}|5([0-3][0-9]{6}|4([0-6][0-9]{5}|7([0-6][0-9]{4}|7([0-4][0-9]{3}|5([0-7][0-9]{2}|80[0-7])))))))))))))))))"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_uint8():
    run_range("uint8", "0..255")


def test_xml_uint16():
    run_range("uint16", "0..65535")


def test_xml_uint32():
    run_range("uint32", "0..4294967295")


def test_xml_uint64():
    yang = Module("example", children=[Leaf("test", "uint64")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "([0-9]{1,19}|1([0-7][0-9]{18}|8([0-3][0-9]{17}|4([0-3][0-9]{16}|4([0-5][0-9]{15}|6([0-6][0-9]{14}|7([0-3][0-9]{13}|4([0-3][0-9]{12}|40([0-6][0-9]{10}|7([0-2][0-9]{9}|3([0-6][0-9]{8}|70([0-8][0-9]{6}|9([0-4][0-9]{5}|5([0-4][0-9]{4}|5(0[0-9]{3}|1([0-5][0-9]{2}|6(0[0-9]|1[0-5])))))))))))))))))"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_decimal64():
    yang = Module("example", children=[Leaf("test", "decimal64", fraction_digits=2, value_range="-100.00..100.00")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_pattern_string():
    yang = Module("example", children=[Leaf("test", "string", pattern="[a-zA-Z0-9\\-]+")]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "[a-zA-Z0-9\\-]+"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)

@pytest.mark.skip(reason="Not supported yet")
def test_xml_two_pattern_string():
    yang = Module("example", children=[Leaf("test", "string", pattern=["[a-z]+", "[0-9]+"])]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "([a-z]+)([0-9]+)"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_typedef():
    yang = Module("example", children=[
        Typedef("test-type", "string", pattern="[a-zA-Z0-9\\-]+"),
        Leaf("test", "test-type")
    ]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "[a-zA-Z0-9\\-]+"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_union_strings_no_patterns():
    yang = Module("example", children=[Leaf("test", "union", union_types=["string", "string"])]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


@pytest.mark.skip(reason="We dont add wildcard for non string matches")
def test_xml_union_strings_one_pattern():
    yang = Module("example", children=[Leaf("test", "union", union_types=['string { pattern "1|2"; }', 'string'])]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "(1|2)|(.*)"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_union_strings():
    yang = Module("example", children=[Leaf("test", "union", union_types=['string { pattern "1|2"; }', 'string { pattern "3|4"; }'])]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "(1|2)|(3|4)"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_union_int():
    yang = Module("example", children=[Leaf("test", "union", union_types=['int8', 'uint8'])]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "((-([1-9][0-9]?|1[01][0-9]|12[0-8])|0|([1-9][0-9]?|1[01][0-9]|12[0-7])))|((0|([1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5])))"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)


def test_xml_union_union_strings():
    yang = Module("example", children=[
        Typedef("type1", "union", union_types=[
            'string { pattern "1|2"; }',
            'string { pattern "3|4"; }'
        ]),
        Typedef("type2", "union", union_types=[
            'string { pattern "5|6"; }',
            'string { pattern "7|8"; }'
        ]),
        Leaf("test", "union", union_types=[
            "type1",
            "type2"
        ])
    ]).render()
    print(yang)
    expected = dict_to_xml("example", [{"name": "test", "mode": "rw", "pattern": "((1|2)|(3|4))|((5|6)|(7|8))"}])
    output = pyang(yang, format="apteryx-xml")
    assert_xml_equal(output, expected)
