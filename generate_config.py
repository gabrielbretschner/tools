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

    for k,v in the_dict.items():
        if k == keys[0]:
            the_dict[k] = update_dict(v, keys[1:], value)
    return the_dict


@click.command()
@click.option('--template', required=True, help='Template config in yaml format.', type=click.File())
@click.option('--output', required=True, help="Output base-filename", type=click.Path(exists=False))
@click.option('--key', required=True, help="the key to replace (use . to delimit levels)", type=click.STRING)
@click.option('--values', required=True, help='the values to set it to', type=ListClickType())
@click.option('--names', default=" ", help="Name for each value for file name", type=ListClickType())
def generate_config(template, output, key, values, names):
    """Generate new config from template by replacing given key with values."""
    if len(names) > 0:
        assert len(values) == len(names), "each value needs a name specified"
    else:
        names = values

    config_template = load(template, Loader=Loader)
    keys = key.split('.')
    for name, value in zip(names, values):
        new_config = update_dict(config_template, keys, value)
        with open("%s.%s.yaml" % (output, name), "w") as f:
            f.write(dump(new_config, explicit_start=True))


if __name__ == '__main__':
    generate_config()
