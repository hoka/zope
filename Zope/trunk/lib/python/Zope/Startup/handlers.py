import os

# top-level key handlers

def _setenv(name, value):
    if isinstance(value, str):
        os.environ[name] = value
    else:
        os.environ[name] = `value`

def debug_mode(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    return value

def enable_product_installation(value):
    value and _setenv('FORCE_PRODUCT_LOAD', '1')
    return value

def locale(value):
    import locale
    locale.setlocale(locale.LC_ALL, value)
    return value

def zserver_read_only_mode(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def automatically_quote_dtml_request_data(value):
    not value and _setenv('ZOPE_DTML_REQUEST_AUTOQUOTE', '0')
    return value

def skip_authentication_checking(value):
    value and _setenv('ZSP_AUTHENTICATED_SKIP', '1')
    return value

def skip_ownership_checking(value):
    value and _setenv('ZSP_OWNEROUS_SKIP', '1')
    return value

def maximum_number_of_session_objects(value):
    default = 1000
    value not in (None, default) and _setenv('ZSESSION_OBJECT_LIMIT', value)
    return value

def session_add_notify_script_path(value):
    value is not None and _setenv('ZSESSION_ADD_NOTIFY', value)
    return value

def session_delete_notify_script_path(value):
    value is not None and _setenv('ZSESSION_DEL_NOTIFY', value)
    return value

def session_timeout_minutes(value):
    default = 20
    value not in (None, default) and _setenv('ZSESSION_TIMEOUT_MINS', value)
    return value

def suppress_all_access_rules(value):
    value and _setenv('SUPPRESS_ACCESSRULE', value)
    return value

def suppress_all_site_roots(value):
    value and _setenv('SUPPRESS_SITEROOT', value)
    return value

def database_quota_size(value):
    value and _setenv('ZOPE_DATABASE_QUOTA', value)
    return value

def read_only_database(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def zeo_client_name(value):
    value and _setenv('ZEO_CLIENT', value)
    return value

def structured_text_header_level(value):
    value is not None and _setenv('STX_DEFAULT_LEVEL', value)
    return value

def maximum_security_manager_stack_size(value):
    value is not None and _setenv('Z_MAX_STACK_SIZE', value)
    return value

def publisher_profile_file(value):
    value is not None and _setenv('PROFILE_PUBLISHER', value)
    return value

def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value

def security_policy_implementation(value):
    value not in ('C', None) and _setenv('ZOPE_SECURITY_POLICY', value)

# server handlers

def root_handler(config):
    """ Mutate the configuration with defaults and perform
    fixups of values that require knowledge about configuration
    values outside of their context. """

    # Add any product directories not already in Products.__path__.
    # Directories are added in the order
    if config.products:
        import Products
        L = []
        for d in config.products + Products.__path__:
            if d not in L:
                L.append(d)
        Products.__path__[:] = L

    # if no servers are defined, create default http server and ftp server
    if not config.servers:
        import ZServer.datatypes
        config.servers = [
            ZServer.datatypes.HTTPServerFactory(_DummyServerConfig(8080)),
            ZServer.datatypes.FTPServerFactory(_DummyServerConfig(8021)),
            ]

    # prepare servers:
    for factory in config.servers:
        factory.prepare(config.ip_address or '',
                        config.dns_resolver,
                        "Zope",
                        config.cgi_environment,
                        config.port_base)


class _DummyServerConfig:
    class _Thing:
        pass

    def __init__(self, port):
        import socket
        self.address = self._Thing()
        self.address.family = socket.AF_INET
        self.address.address = '', port
        self.force_connection_close = 0


def handleConfig(config, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)
