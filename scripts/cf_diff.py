#!/usr/bin/env python

import os, boto, boto.cloudformation, difflib, sys, json
from optparse import OptionParser
from boto.exception import BotoServerError
from boto.s3.connection import S3Connection
from termcolor import colored

def problems(msg):
    print("Problem: %s" % msg)
    exit(1)

def get_stack(opt):
    cf = boto.cloudformation.connect_to_region(opt.region)
    try:
        return cf.describe_stacks(stack_name_or_id=opt.stack)[0]
    except BotoServerError, e:
        problems("Some kinda EC2 drama %s" % e.message)

def get_params(stack):
    params = dict()
    for param in stack.parameters:
        params[param.key] = param.value

    return params

def extract_defaults(template):
    obj = json.loads(template)
    defaults = dict()
    for name, params in obj['Parameters'].items():
        if 'Default' in params:
            defaults[name] = params['Default']
    return defaults

def template_from_s3(opt):
    # eu-central-1 is kinda fucked up
    conn = None
    if opt.region == 'eu-central-1':
        os.environ['S3_USE_SIGV4'] = 'True'
        conn = S3Connection(is_secure=False,host='s3.eu-central-1.amazonaws.com')
    else:
        conn = boto.connect_s3()
    bucket = conn.get_bucket(opt.bucket)
    template = bucket.get_key("%s.json" % (opt.template))
    if 'S3_USE_SIGV4' in os.environ:
        del os.environ['S3_USE_SIGV4']
    if not template:
        problems("Unable to find S3 template %s" % (opt.template))
    else:
        return template.get_contents_as_string()

# should result in similarily formatted files
def json_massage(things):
    obj = json.loads(things)
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

def param_builder(option, opt, value, parser):
    k, v = value.split('=')
    if parser.values.params:
        parser.values.params[k] = v
    else:
        parser.values.params = {k: v}

def main():
    parser = OptionParser()
    parser.add_option('--bucket',
                      dest='bucket',
                      help='Bucket where templates may be found')
    parser.add_option('--region',
                      dest='region',
                      help='AWS Region',
                      default=os.environ['AWS_DEFAULT_REGION'])
    parser.add_option('--stack',
                      dest='stack',
                      type='string',
                      help='Stack name to check')
    parser.add_option('--template',
                      type='string',
                      dest='template',
                      help='Template name to check. Defaults to stack name.')
    parser.add_option('--param',
                      type='string',
                      dest='params',
                      action='callback',
                      callback=param_builder,
                      help='A key=value list of params to verify. May be specified multiple times.')

    opt, args = parser.parse_args()
    if not opt.stack or not opt.bucket:
        problems("stack and bucket must be defined")
    
    if not opt.template:
        opt.template = opt.stack

    if not opt.params:
        opt.params = dict()

    bucket_template = json_massage(template_from_s3(opt))

    stack = get_stack(opt)
    cloud_template = json_massage(stack.get_template()['GetTemplateResponse']['GetTemplateResult']['TemplateBody'])
    cloud_params = get_params(stack)
    cloud_defaults = extract_defaults(cloud_template)

    dat_diff = difflib.unified_diff(bucket_template.splitlines(), 
                                    cloud_template.splitlines(),
                                    fromfile='bucket',
                                    tofile='cloudformation')

    rc = 0
    for line in dat_diff:
        # if we are in here at all then there are differences
        if rc == 0:
            rc = 1
    
        if line[0] == '+':
            print colored(line, 'green')
        elif line[0] == '-':
            print colored(line, 'red')
        else:
            print line
    
    for k, v in opt.params.items():
        if k in cloud_params:
            if v != cloud_params[k]:
                if rc == 0:
                    rc = 1
                print colored("- %s=%s" % (k, v), 'red')
                print colored("+ %s=%s" % (k, cloud_params[k]), 'green')
        else:
            if rc == 0:
                rc = 1
            print colored("- %s=%s" % (k, v), 'red')

    for k, v in cloud_params.items():
        if v != '' and cloud_defaults.get(k) != v and k not in opt.params:
            if rc == 0:
                rc = 1
            print colored("+ %s=%s" % (k, v), 'green')

    sys.exit(rc)

if __name__ == "__main__":
    main()
