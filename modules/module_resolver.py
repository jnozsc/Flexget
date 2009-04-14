import logging

__pychecker__ = 'unusednames=parser'

log = logging.getLogger('resolver')

class ResolverException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ModuleResolver:

    def register(self, manager, parser):
        manager.register('resolver', builtin=True)
        manager.add_feed_event('resolve', before='download')

    def feed_resolve(self, feed):
        # no resolves in unit test mode
        if feed.manager.unit_test: 
            return
        self.entries(feed)

    def resolvable(self, feed, entry):
        """Return True if entry is resolvable by registered resolver."""
        for resolver in feed.manager.get_modules_by_group('resolver'):
            if resolver['instance'].resolvable(self, entry):
                return True
        return False

    def resolve(self, feed, entry):
        """Resolves given entry url. Raises ResolverException if resolve failed."""
        tries = 0
        while self.resolvable(feed, entry):
            tries += 1
            if (tries > 300):
                raise ResolverException('Resolve was left in infinite loop while resolving %s, some resolver is returning always True' % entry)
            for resolver in feed.manager.get_modules_by_group('resolver'):
                name = resolver['name']
                if resolver['instance'].resolvable(feed, entry):
                    try:
                        resolver['instance'].resolve(feed, entry)
                        log.info('Resolved \'%s\' to %s (with %s)' % (entry['title'], entry['url'], name))
                    except ResolverException, r:
                        # increase failcount
                        #count = self.shared_cache.storedefault(entry['url'], 1)
                        #count += 1
                        raise ResolverException('Resolver %s failed: %s' % (name, r.value))
                    except Exception, e:
                        log.exception(e)
                        raise ResolverException('%s: Internal error with url %s' % (name, entry['url']))

    def entries(self, feed):
        """Resolves all accepted entries in feed. Since this causes many requests to sites, use with caution."""
        for entry in feed.accepted:
            try:
                self.resolve(feed, entry)
            except ResolverException, e:
                log.warn(e.value)
                feed.fail(entry)
