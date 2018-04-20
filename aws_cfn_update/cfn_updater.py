import sys
import cfn_flip
import os.path
import json
import collections


class CfnUpdater(object):
    """
    base updater of cloudformation templates.
    """

    def __init__(self):
        self.basename = None
        self.template = False
        self.template = None
        self.template_format = None
        self.dirty = False
        self.dry_run = False
        self.verbose = False
        self._filename = None

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = filename
        parts = os.path.splitext(os.path.basename(filename))
        self.basename = parts[0]
        self.template_format = parts[1]
        self.template = None
        self.dirty = False
        if self.template_format not in ('.json', '.yml', '.yaml'):
            raise ValueError('%s has no .json, .yaml or .yml extension.' % filename)

    def load(self):
        self.dirty = False
        self.template = None
        with open(self.filename, 'r') as f:
            if self.template_format == '.json':
                self.template = json.load(f, object_pairs_hook=collections.OrderedDict)
            else:
                self.template = json.loads(cfn_flip.to_json(f), object_pairs_hook=collections.OrderedDict)

    def is_cloudformation_template(self):
        """
        returns true if the `self.template` is a AWS CloudFormation template
        """
        return 'AWSTemplateFormatVersion' in self.template

    def write(self):
        """
        write modified the CloudFormation template. It will retain it's original
        format (yaml or json) but will loose formatting and comments.
        """
        if not self.dirty and self.verbose:
            sys.stderr.write('INFO: no changes in {}\n'.format(self.filename))
            return

        if self.dry_run:
            return

        body = json.dumps(self.template, separators=(',', ': '), indent=2)
        if self.template_format == '.yaml':
            body = cfn_flip.to_yaml(body)
        with open(self.filename, 'w') as f:
            f.write(body)

    def update_template(self):
        """
        implement the update logic of `self.template`. Set self.dirty to True, if you modified.
        """
        pass

    def update(self, path):
        """
        recursively updates all the cloudformation templates in the specified `path`. `path` may be a file,
        a directory or a list of paths.
        """
        if isinstance(path, list):
            for p in path:
                self.update(p)
        elif os.path.isfile(path):
            if path.endswith('.yml') or path.endswith('.yaml') or path.endswith('.json'):
                self.filename = path
                self.load()
                if self.is_cloudformation_template():
                    self.update_template()
                    self.write()
                else:
                    if self.verbose:
                        sys.stderr.write('INFO: skipping {} as it is not a CloudFormation template\n'.format(path))
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    self.update(os.path.join(root, f))
        else:
            sys.stderr.write('ERROR: {} is not a file or directory\n'.format(path))
            sys.exit(1)