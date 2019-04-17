import click
from list_click_type import ListClickType
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def update_dict(the_dict, keys, value):
    if len(keys) == 0:
        return value
    if isinstance(the_dict, list):
        keys[0] = int(keys[0])

    the_dict[keys[0]] = update_dict(the_dict[keys[0]], keys[1:], value)
    return the_dict


@click.command()
@click.option('--template', required=True, help='Template config in yaml format.', type=click.File())
@click.option('--output', required=True, help="Output base-filename", type=click.Path(exists=False))
@click.option('--key', required=True, multiple=True, help="the key to replace (use . to delimit levels)", type=click.STRING)
@click.option('--values', required=True, multiple=True, help='the values to set it to', type=ListClickType())
@click.option('--names', default=" ", help="Name for each value for file name", type=ListClickType())
def generate_config(template, output, key, values, names):
    """Generate new config from template by replacing given key with values."""
    if isinstance(key, tuple):
        assert isinstance(values, tuple) and len(key) == len(values)
        key = list(key)
        values = list(values)
    else:
        key = [key]
        values = [values]

    if len(names) > 0:
        for v in values:
            assert len(v) == len(names), "each value needs a name specified"
    else:
        names = values[0]

    config_template = load(template, Loader=Loader)
    configs = [None] * len(names)
    for k, v in zip(key, values):
        keys = k.split('.')
        for i, value in enumerate(v):
            new_config = update_dict(config_template.copy(), keys, value)
            configs[i] = new_config

    for name, config in zip(names, configs):
        with open("%s.%s.yaml" % (output, name), "w") as f:
            f.write(dump(config, explicit_start=True))


if __name__ == '__main__':
    generate_config()
