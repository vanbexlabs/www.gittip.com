"""Wireup
"""
import os
import sys

import aspen
import balanced
import gittip
import raven
import psycopg2
import stripe
import gittip.mixpanel
from gittip.postgres import PostgresManager
from psycopg2.extensions import cursor as RegularCursor


def canonical():
    gittip.canonical_scheme = os.environ['CANONICAL_SCHEME']
    gittip.canonical_host = os.environ['CANONICAL_HOST']


# wireup.db() should only ever be called once by the application
def db():
    dburl = os.environ['DATABASE_URL']
    maxconn = int(os.environ['DATABASE_MAXCONN'])
    gittip.db = PostgresManager(dburl, maxconn=maxconn)

    # register hstore type (but don't use RealDictCursor)
    with gittip.db.get_connection() as conn:
        curs = conn.cursor(cursor_factory=RegularCursor)
        psycopg2.extras.register_hstore(curs, globally=True, unicode=True)

    return gittip.db


def billing():
    stripe.api_key= os.environ['STRIPE_SECRET_API_KEY']
    stripe.publishable_api_key= os.environ['STRIPE_PUBLISHABLE_API_KEY']
    balanced.configure(os.environ['BALANCED_API_SECRET'])


def username_restrictions(website):
    gittip.RESTRICTED_USERNAMES = os.listdir(website.www_root)


def sentry(website):
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn is not None:
        sentry = raven.Client(sentry_dsn)
        def tell_sentry(request):
            cls, response = sys.exc_info()[:2]
            if cls is aspen.Response:
                if response.code < 500:
                    return

            kw = {'extra': { "filepath": request.fs
                           , "request": str(request).splitlines()
                            }}
            exc = sentry.captureException(**kw)
            ident = sentry.get_ident(exc)
            aspen.log_dammit("Exception reference: " + ident)
        website.hooks.error_early += [tell_sentry]


def mixpanel(website):
    website.mixpanel_token = os.environ['MIXPANEL_TOKEN']
    gittip.mixpanel.MIXPANEL_TOKEN = os.environ['MIXPANEL_TOKEN']

def nanswers():
    from gittip.models import participant
    participant.NANSWERS_THRESHOLD = int(os.environ['NANSWERS_THRESHOLD'])

def nmembers(website):
    from gittip.models import community
    community.NMEMBERS_THRESHOLD = int(os.environ['NMEMBERS_THRESHOLD'])
    website.NMEMBERS_THRESHOLD = community.NMEMBERS_THRESHOLD
