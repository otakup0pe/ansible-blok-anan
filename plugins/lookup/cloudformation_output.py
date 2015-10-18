#!/usr/bin/env python

import boto.cloudformation, sys
from boto.exception import BotoServerError

def cloudformation_lookup(region, stack_name, key):
    cf = boto.cloudformation.connect_to_region(region)
    try:
        stack = cf.describe_stacks(stack_name_or_id=stack_name)[0]
    except BotoServerError, e:
        if e.code == 'ValidationError' and e.message.find('does not exist') == -1:
            raise(e)
        else:
            return ''
    for output in stack.outputs:
        if output.key == key:
            return output.value
    return ''

class LookupModule(object):
    def __init__(self, basedir=None):
        self.basedir = basedir

    def run(self, terms, inject=None, basedir=None, vars={}):
        region, stack_name, output = terms.split('/')
        return [cloudformation_lookup(region, stack_name, output)]


def main():
    region, stack_name, output = sys.argv[1:]
    print cloudformation_lookup(region, stack_name, output)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("cloudformation_output.py <region> <stack> <output>")
        sys.exit(1)

    main()
