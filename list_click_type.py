import click

class ListClickType(click.ParamType):
    name = "list"

    def convert(self, value, param, ctx):
        if "," in value:
            return value.split(",")
        return value.split()
