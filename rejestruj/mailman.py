#!/usr/bin/python
# -*- coding: utf-8 -*-

import xmlrpclib

#-----------------------------------------------------------------------------

class MailLists:
    def __init__(self, config, email, hsmember = False):
        self.config = config
        self.email = email
        self.is_member = hsmember
        self.url = config['MAILMAN_XMLRPC_URL']
        self.rpc = xmlrpclib.Server(self.url)

        result = self.rpc.mailman.membership(self.email)
        self.internal_lists = result['internal']
        self.public_lists = result['public']
        # internal:
        #   name:
        #     description: "..."
        #     subscribed: true | false
        #     address: "...@..."
        #   ...
        # public:
        #   name:
        #     description: "..."
        #     subscribed: true | false
        #     address: "...@..."
        #   ...

    def lists(self):
        for (name, info) in self.public_lists.iteritems():
            yield {
                "name": name,
                "description": info['description'],
                "address":     info['address'],
                "subscribed":  info['subscribed'],
            }
        for (name, info) in self.internal_lists.iteritems():
            # skip if not a HS member and not subscribed to the list (to allow
            # unsubscribing from an internal list, but not subscribing back)
            if self.is_member or info['subscribed']:
                yield {
                    "name": name,
                    "description": info['description'],
                    "address":     info['address'],
                    "subscribed":  info['subscribed'],
                }

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
