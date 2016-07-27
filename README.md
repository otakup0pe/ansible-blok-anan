Cloud Building Blocks
---------------------

# etymology

`anan` is an old aramaic term for cloud.
`blok` translates loosely as "block" in a few languages.

----

# Context

This repository contains small snippets and building bloks I make use of on some cloud adjacent side projects. Thus far it is just some Cloudformation templates and some Ansible extensions but that will probably change over time.

# Ansible role

As it stands the Ansible role will take a CloudFormation template, upload it to a S3 bucket, and generate a stack with it. The S3 bucket will be created (with a per-region name) if it does not already exist. In order to ensure that copies of the CloudFormation stacks remain available on a per-stack basis, ensure that each stack / template combination is unique.

## Required variables

* `cloudformation_stack` is the name of the stack as it will be created
* `cloudformation_template` is the pathname (relative to the ansible entrypoint) of the CloudFormation template itself. The S3 object name will be interpreted as the basename of this file path.
* `cloudformation_bucket` is the prefix name of the S3 bucket that will be created to store templates.

## Optional variables

* `cloudformation_region` defaults to `us-east-1`
* `cloudformation_scratch` should definitely be changed from `/tmp` on multi user systems
* `cloudformation_disable_rollback` is disabled by default

# Ansible extensions

## Filter plugin

The one hilariously trivial filter plugin, `basename`, is used only to extract the basename of a given filepath. Kind of surprised this wasn't stock Ansible.

## Lookup plugin

This plugin may be used to extract output parameters from CloudFormation stacks. It takes three forward-slash separated arguments - aws region, stack name, and output parameters name. This could be used in an Ansible playbook as follows.

    lookup('cloudformation_output', cloudformation_region + '/yoloblog/ZoneId')

## Module

The `route53_to_gandi` module will extract the `NS` records from a given Route53 zone id and update the corresponding DNS settings on Gandi registered domains. It has some optional and some required arguments.

* `zone_id` is required and must exist
* `domain` must be speciefied and be registered with Gandi
* `aws_key` will be looked up by environment variable if not specified
* `aws_secret` will be looked up by environment variable if not specified
* `gandi_key` if not specified the `GANDI_KEY` environment variable will be used

# CloudFormation Templates

## tumblr

This will create a simple stack comprised of a Route53 zone and some records pointing at Tumblr. It will optionally create a `TXT` record for Google Site registration. It will also optionally create an S3 bucket and associated Route53 domain for a `www` redirect page. The one output parameter is the Route53 zone id. The following parameters are supported.

* `DomainName` is the domain being used.
* `TTL` is the TTL for the records. Defaults to 1800s.
* `GoogleSiteVerificationCode` is for the code that Google will give you. The default, an empty string, will result in no `TXT` record.
* `WWWAlias` is used to enable a WWW redirect domain and defaults to `no`.

## site

This will create a simple stack comprised of S3 buckets and Route53 resource records in order to facilitate hosting static web sites in S3. This template assumes that a Route53 zone already exists (see `domain` template). The only output parameter is the ZoneId. The following parameters are supported.

* `DomainName` is the domain being used.
* `DomainPrefix` if you are not using the top level domain. Defaults safely to an empty string.
* `TTL` is the TTL for the records. Defaults to 1800s.
* `WWWAlias` is used to enable a WWW redirect domain and defaults to `no`.
* `TumblrBlog` will create a subdomain `CNAME` record called `blog` and point it at Tumblr. Defaults to `no`.
* `GoogleSiteVerificationCode` is for the code that Google will give you. The default, an empty string, will result in no `TXT` record.
* `IndexPage` is used to specify the default S3 object and defaults to `index.html`.
* `ProblemPage` is used to specify the page used during errors and defaults to `problems.html`.
* `PublicAccess` is used to lock down the bucket. Note that if you do so, a S3 bucket policy will need to be created (see `access` template).
* `CreateDomain` is used to determine whether or not we are actually creating the Route53 zone. If this is set then `ZoneId` will be ignored. This defaults to `no`.
* `ZoneId` is used if we are not creating the domain. If `CreateDomain` is _no_ then this must be set.
* `RedirectTo` is used to have the S3 bucket redirect to another site.
* `CNAMETo` is used to have a CNAME redirect. Note this will only work if there is a `DomainPrefix` set - you cannot use a CNAME otherwise.

## access

This is an Ansible template that generates an IP whitelist S3 bucket policy. It has no output parameters and supports the following input parameters.

* `DomainName` is the domain being used.
* `DomainPrefix` if you are not using the top level domain. Defaults safely to an empty string.
* `PublicAccess` is used to lock down the bucket. Note that if you do so, a S3 bucket policy will need to be created (see `access` template).

As this is an Ansible template, it also requires the `restrict_site_ips` parameter to be set when it is compiled. This is a list of IP's to add to the whitelist.
