r"""
Module that encapsulates the cache / io operations
"""

class FileSystemPipeline:
    def __init__(self, owner):
        self._owner = owner
        self.contents = []

    def get(self, key):
        pass

    def set(self, key, value):
        self.contents.append(str(key))
        self.contents.append(str(value))

    def execute(self):
        self._owner.handle.write('\n'.join(self.contents))
        self.contents = []

class FileSystemCache:
    def __init__(self, fname, as_input=False):
        self._fname = fname
        self.handle = open(fname, 'r' if as_input else 'w')

    def pipeline(self):
        return FileSystemPipeline(self)
    
def connect(args, as_input=True):
    if args.cache_type == 'redis':
        import redis
        if args.cache_ssl == 'yes':
            return redis.Redis(\
                host=args.cache_name,
                port=args.cache_port,
                password=args.cache_key,
                ssl_cert_reqs=u'none', #-- or specify location of certs
                ssl=True)
        else:
            return redis.Redis(\
                host=args.cache_name,
                port=args.cache_port,
                password=args.cache_key)
        
    elif args.cache_type == 'filesystem':
        return FileSystemCache(args.cache_path, as_input=as_input)
    else:
        raise RuntimeError(f'Invalid cache type: {args.cache_type}')
