# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from redis import StrictRedis


class LambdaError(Exception):
    def __init__(self, code, msg, context):
        self.code = code
        self.context = context
        self.custom_message = msg
        super(LambdaError, self).__init__(self.jsonify())

    def jsonify(self):
        return dict(type=self.__class__.__name__, message=self.custom_message, requestid=self.context.requestId)


class AuthError(LambdaException):
    def __init__(self, msg=None, **kwargs):
        super(AuthError, self).__init__(401, msg or 'Auth error', **kwargs)


# Assuming a shared Redis instance that stores user auth and tokens
user_auth = StrictRedis.from_url(
        url=os.environ['REDIS_AUTH_HOST'],
        socket_timeout=os.environ['REDIS_SOCKET_TIMEOUT'],
        max_connections=os.environ['REDIS_CONNECTION_POOL']
    )

# Assuming a shared Redis instance that stores feature switches from backoffice
features = StrictRedis.from_url(
        url=os.environ['REDIS_FEATURES_HOST'],
        socket_timeout=os.environ['REDIS_SOCKET_TIMEOUT'],
        max_connections=os.environ['REDIS_CONNECTION_POOL']
    )


def lambda_handler(event, context):
    # Get the globally available features
    active_features = features.smembers('global_features')

    # Check whether the call is authorized
    if 'headers' in event and 'Authorization' in event['headers']:
        # If so, check that the Authorization is properly formatted
        header = event['headers']['Authorization'].split(' ')
        if len(header) != 2:
            raise AuthError(context=context)

        # Try to get the associated user_id from the stored token; if empty, token is expired
        user_id = user_auth.get(header[1])
        if not user_id:
            raise AuthError(context=context)

        # Add both global features and the specific ones for a user, always checking that they are active
        active_features = features.smembers('global_features') | features.sinter('active_features', 'features:user:{}'.format(user_id))
     
    return dict(active_features=list(active_features))

