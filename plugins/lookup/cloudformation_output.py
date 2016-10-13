#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import boto.cloudformation, sys
from boto.exception import BotoServerError
from ansible.plugins.lookup import LookupBase

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

class LookupModule(LookupBase):

    def run(self, terms, **kwargs):
        region, stack_name, output = terms[0].split('/')
        return [cloudformation_lookup(region, stack_name, output)]
