class YangNode:
    def render(self, indent=0):
        raise NotImplementedError


class Leaf(YangNode):
    def __init__(self, name, yang_type=None, enumeration=None, pattern=None, union_types=None, default=None, mandatory=False, fraction_digits=None, value_range=None):
        self.name = name
        self.yang_type = yang_type
        self.enumeration = enumeration or []
        if isinstance(pattern, str):
            self.pattern = [pattern]
        else:
            self.pattern = pattern or []
        self.union_types = union_types or []  # can contain strings or Leaf/Typedef instances
        self.default = default
        self.mandatory = mandatory
        self.fraction_digits = fraction_digits
        self.value_range = value_range

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}leaf {self.name} {{']
        if self.enumeration:
            lines.append(f'{ind}  type enumeration {{')
            for e in self.enumeration:
                lines.append(f'{ind}    enum {e};')
            lines.append(f'{ind}  }}')
        elif self.union_types:
            lines.append(f'{ind}  type union {{')
            for t in self.union_types:
                if isinstance(t, (Leaf, Typedef)):
                    # render nested type block without semicolon
                    nested = t.render(indent + 4)
                    # remove the leading 'leaf name {' or 'typedef name {' line for proper union
                    nested_lines = nested.split('\n')[1:-1]  # skip first and last line
                    for nl in nested_lines:
                        lines.append(f'{ind}    {nl.strip()}')
                else:
                    t_str = t.strip()
                    if '{' in t_str:
                        lines.append(f'{ind}    type {t_str}')
                    else:
                        lines.append(f'{ind}    type {t_str};')
            lines.append(f'{ind}  }}')
        elif self.yang_type == 'string' and self.pattern:
            lines.append(f'{ind}  type string {{')
            for p in self.pattern:
                lines.append(f'{ind}    pattern "{p}";')
            lines.append(f'{ind}  }}')
        elif self.yang_type == 'decimal64':
            lines.append(f'{ind}  type decimal64 {{')
            if self.fraction_digits is not None:
                lines.append(f'{ind}    fraction-digits {self.fraction_digits};')
            if self.value_range is not None:
                lines.append(f'{ind}    range "{self.value_range}";')
            lines.append(f'{ind}  }}')
        else:
            lines.append(f'{ind}  type {self.yang_type};')
        if self.default is not None:
            lines.append(f'{ind}  default "{self.default}";')
        if self.mandatory:
            lines.append(f'{ind}  mandatory true;')
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class LeafList(YangNode):
    def __init__(self, name, yang_type, min_elements=None, max_elements=None):
        self.name = name
        self.yang_type = yang_type
        self.min_elements = min_elements
        self.max_elements = max_elements

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}leaf-list {self.name} {{']
        lines.append(f'{ind}  type {self.yang_type};')
        if self.min_elements is not None:
            lines.append(f'{ind}  min-elements {self.min_elements};')
        if self.max_elements is not None:
            lines.append(f'{ind}  max-elements {self.max_elements};')
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class List(YangNode):
    def __init__(self, name, keys=None, children=None):
        self.name = name
        self.keys = keys or []
        self.children = children or []

    def add(self, node):
        self.children.append(node)

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}list {self.name} {{']
        if self.keys:
            keys_str = ' '.join(self.keys)
            lines.append(f'{ind}  key "{keys_str}";')
        for child in self.children:
            lines.append(child.render(indent + 2))
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class Container(YangNode):
    def __init__(self, name, children=None, presence=None):
        self.name = name
        self.children = children or []
        self.presence = presence

    def add(self, node):
        self.children.append(node)

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}container {self.name} {{']
        if self.presence:
            lines.append(f'{ind}  presence "{self.presence}";')
        for child in self.children:
            lines.append(child.render(indent + 2))
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class Choice(YangNode):
    def __init__(self, name, cases=None):
        self.name = name
        self.cases = cases or []

    def add_case(self, case):
        self.cases.append(case)

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}choice {self.name} {{']
        for case in self.cases:
            lines.append(case.render(indent + 2))
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class Case(YangNode):
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

    def add(self, node):
        self.children.append(node)

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}case {self.name} {{']
        for child in self.children:
            lines.append(child.render(indent + 2))
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class Typedef(YangNode):
    def __init__(self, name, base_type, pattern=None, union_types=None):
        self.name = name
        self.base_type = base_type
        if isinstance(pattern, str):
            self.pattern = [pattern]
        else:
            self.pattern = pattern or []
        self.union_types = union_types or []  # can contain strings or Leaf/Typedef instances

    def render(self, indent=0):
        ind = ' ' * indent
        lines = [f'{ind}typedef {self.name} {{']
        if self.union_types:
            lines.append(f'{ind}  type union {{')
            for t in self.union_types:
                if isinstance(t, (Leaf, Typedef)):
                    nested = t.render(indent + 4)
                    nested_lines = nested.split('\n')[1:-1]
                    for nl in nested_lines:
                        lines.append(f'{ind}    {nl.strip()}')
                else:
                    t_str = t.strip()
                    if '{' in t_str:
                        lines.append(f'{ind}    type {t_str}')
                    else:
                        lines.append(f'{ind}    type {t_str};')
            lines.append(f'{ind}  }}')
        elif self.pattern:
            lines.append(f'{ind}  type {self.base_type} {{')
            for p in self.pattern:
                lines.append(f'{ind}    pattern "{p}";')
            lines.append(f'{ind}  }}')
        else:
            lines.append(f'{ind}  type {self.base_type};')
        lines.append(f'{ind}}}')
        return '\n'.join(lines)


class Module(YangNode):
    def __init__(self, name, namespace=None, prefix=None, children=None, imports=None, includes=None):
        self.name = name
        self.namespace = namespace or f'http://{name}.com/{name}'
        self.prefix = prefix or name
        self.children = children or []
        self.imports = imports or []
        self.includes = includes or []

    def add(self, node):
        self.children.append(node)

    def render(self, indent=0):
        lines = [f'module {self.name} {{', f'  namespace "{self.namespace}";', f'  prefix {self.prefix};', '']
        for imp in self.imports:
            lines.append(f'  import {imp};')
        for inc in self.includes:
            lines.append(f'  include {inc};')
        for child in self.children:
            lines.append(child.render(2))
        lines.append('}')
        return '\n'.join(lines)
