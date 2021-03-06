"""Universe configuration builder."""
import sys, os, logging, logging.config, ConfigParser
# from optparse import OptionParser
from cm.util import string_as_bool
from cm.util import misc
from cm.util import paths

log = logging.getLogger( 'cloudman' )

def resolve_path( path, root ):
    """If 'path' is relative make absolute by prepending 'root'"""
    if not( os.path.isabs( path ) ):
        path = os.path.join( root, path )
    return path
      
class ConfigurationError( Exception ):
    pass

class Configuration( object ):
    def __init__( self, **kwargs ):
        self.config_dict = kwargs
        self.root = kwargs.get( 'root_dir', '.' )                   
        # Where dataset files are stored
        self.id_secret = kwargs.get( "id_secret", "USING THE DEFAULT IS NOT SECURE!" )
        self.use_remote_user = string_as_bool( kwargs.get( "use_remote_user", "False" ) )
        self.require_login = string_as_bool( kwargs.get( "require_login", "False" ) )
        self.template_path = resolve_path( kwargs.get( "template_path", "templates" ), self.root )
        self.cloudman_source_file_name = kwargs.get("cloudman_file_name", "cm.tar.gz")
        # self.template_cache = resolve_path( kwargs.get( "template_cache_path", "database/reports/compiled_templates" ), self.root )
        self.sendmail_path = kwargs.get('sendmail_path',"/usr/sbin/sendmail")
        self.brand = kwargs.get( 'brand', None )
        self.wiki_url = kwargs.get( 'wiki_url', "http://g2.trac.bx.psu.edu/" )
        self.GC_url = kwargs.get( 'GC_url', 'http://bitbucket.org/afgane/galaxy-central-gc2/' )
        self.CM_url = kwargs.get( 'GC_url', 'http://bitbucket.org/galaxy/cloudman/' )
        self.bugs_email = kwargs.get( 'bugs_email', "mailto:galaxy-bugs@bx.psu.edu" )
        self.blog_url = kwargs.get( 'blog_url', "http://g2.trac.bx.psu.edu/blog" )
        self.screencasts_url = kwargs.get( 'screencasts_url', "http://g2.trac.bx.psu.edu/wiki/ScreenCasts" )
        #Parse global_conf
        global_conf = kwargs.get( 'global_conf', None )
        global_conf_parser = ConfigParser.ConfigParser()
        if global_conf and "__file__" in global_conf:
            global_conf_parser.read(global_conf['__file__'])
        # Load supported image configuration from a file on the image.
        # This is a dict containing a list of configurations supported by
        # the by system/image. Primarily, this contains a list
        # of apps (available under key 'apps'). This config file allows CloudMan
        # to integrate native and custom support for additional applications.
        # The dict contains default values for backward combatibility.
        self.ic = {'apps': ['cloudman', 'galaxy']} 
        if os.path.exists(paths.IMAGE_CONF_SUPPORT_FILE):
            self.ic = misc.load_yaml_file(paths.IMAGE_CONF_SUPPORT_FILE)
        # Logger is not configured yet so print
        print "Image configuration suports: %s" % self.ic
    def get( self, key, default ):
        return self.config_dict.get( key, default )
    def check( self ):
        # Check that required directories exist
        for path in self.root, self.template_path:
            if not os.path.isdir( path ):
                raise ConfigurationError("Directory does not exist: %s" % path )

def get_database_engine_options( kwargs ):
    """
    Allow options for the SQLAlchemy database engine to be passed by using
    the prefix "database_engine_option_".
    """
    conversions =  {
        'convert_unicode': string_as_bool,
        'pool_timeout': int,
        'echo': string_as_bool,
        'echo_pool': string_as_bool,
        'pool_recycle': int,
        'pool_size': int,
        'max_overflow': int,
        'pool_threadlocal': string_as_bool
    }
    prefix = "database_engine_option_"
    prefix_len = len( prefix )
    rval = {}
    for key, value in kwargs.iteritems():
        if key.startswith( prefix ):
            key = key[prefix_len:]
            if key in conversions:
                value = conversions[key](value)
            rval[ key  ] = value
    return rval

def configure_logging( config ):
    """
    Allow some basic logging configuration to be read from the cherrpy
    config.
    """
    # format = config.get( "log_format", "%(name)s %(levelname)s %(asctime)s %(message)s" )
    format = config.get( "log_format", "[%(levelname)s] %(module)s:%(lineno)d %(asctime)s: %(message)s")
    level = logging._levelNames[ config.get( "log_level", "DEBUG" ) ]
    destination = config.get( "log_destination", "stdout" )
    log.info( "Logging at '%s' level to '%s'" % ( level, destination ) )
    # Get root logger
    root = logging.getLogger()
    # Set level
    root.setLevel( level )
    # Turn down paste httpserver logging
    if level <= logging.DEBUG:
        logging.getLogger( "paste.httpserver.ThreadPool" ).setLevel( logging.WARN )
    # Remove old handlers
    for h in root.handlers[:]: 
        root.removeHandler(h)
    # Create handler
    if destination == "stdout":
        handler = logging.StreamHandler( sys.stdout )
    else:
        handler = logging.FileHandler( destination )
    # Create formatter
    formatter = logging.Formatter( format )    
    # Hook everything up
    handler.setFormatter( formatter )
    root.addHandler( handler )
    
    
