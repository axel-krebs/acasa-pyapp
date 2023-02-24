# Shared web objects
from abc import ABC, abstractmethod
import importlib
import os
from pathlib import Path
from quart import Quart, session, render_template, request
import random
import yaml

SCRIPT_PATH = Path(__name__).parent.resolve()

DEFAULT_CONFIG = { # Defaults taken from Quart API
    "import_name": "DEFAULT",
    "static_url_path": "/",
    "static_folder": "static",
    "static_host": "localhost",
    "host_matching":  False,
    "subdomain_matching": False,
    "template_folder": "templates",
    "instance_path": None,
    "instance_relative_config": False,
    "root_path": None
}

class ContextCache(dict):
    """
        This serves as a helper class to share a caching structure between modules 
        resp. between the Deployment class and the deployables; in the future, it 
        should be replaced by a caching framework resp. distributed cache. Like the
        class Documentstore (s.a.), it can then serve as an interface.
    """
    def __init__(self):
        self._protected_dict = dict()

    def __getitem__(self, key):
        return self._protected_dict[key]
    
    def __setitem__(self, key, value):
        self._protected_dict[key] = value
        return self._protected_dict[key]

class Documentstore(ABC):
    """
        An "interface" for the injected document store, th. i. what the web app expects the underlying implementation 
        to be able to deliver (JSON-store); however, the implemetation can be what it wants to be as long as it delivers
    Args:
        ABC (_type_): _description_
    """
    
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def is_prepared(self):
        """Return True if you want prepare() to be invoked. 
        """
        raise NotImplementedError("Should not happen..")
    
    @abstractmethod
    def prepare(self):
        """Callback: If is_prepared() returns False, this method will be invoked.
        """
        raise NotImplementedError("Should not happen..")

    @abstractmethod
    def get_user_for_cookie(self, cookie):
        raise NotImplementedError("Should not happen..")
    
    @abstractmethod
    def create_user(self, name: str = "", email: str = ""):
        raise NotImplementedError("Should not happen..")

def create_instance(root: Path = SCRIPT_PATH, doc_store: Documentstore = None, global_cache: ContextCache = None) -> Quart:
    """
        A deployment must have a predefined structure, e.g. the config file must be named 'config.yaml' and must have an
        entry 'quart' etc.
    Args:
        root (Path, optional): _description_. Defaults to SCRIPT_PATH.
        doc_store (Documentstore, optional): _description_. Defaults to None.
        global_cache (ContextCache, optional): _description_. Defaults to None.

    Raises:
        RuntimeError: If no web database is provided.

    Returns:
        Quart: An ASGI runtime object to be deployed on a ASGI-compatible server, e.g. uvicorn. 
    """
    if doc_store is None:
        raise RuntimeError("The document store must not be None!")
    elif not doc_store.is_prepared():
        doc_store.prepare()
    else:
        print("DocumentStore was existent and prepared.")

    if global_cache is None:
        global_cache = ContextCache()

    CONFIG_PATH = "{}{}{}".format(root.resolve(), os.sep, "config.yml")
    config = DEFAULT_CONFIG # !!!
    with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
        cfg_text = openfile.read()
        config = yaml.safe_load(cfg_text)
        quart_config = config["quart"]
        # TODO test config values..
        config = quart_config
    root_resolved = root.resolve()
    template_path = "{}{}{}".format(root_resolved, str(os.sep), config["template_folder"]) # need abs. path for jinja2
    static_path = "{}{}{}".format(root_resolved, str(os.sep), config["static_folder"]) # 
    static_url_path = config["static_url_path"]
    web_app = Quart(
        import_name = config["import_name"],
        #root_path = config["root_path"],
        root_path = root_resolved, # assume correct
        static_folder = static_path,
        static_url_path = static_url_path,
        template_folder = template_path
    )
    
    _apply_configuration(web_app, config, doc_store)

    # TODO this is just an intermediate solution: __init__.py cannot implement an I/F!
    root_package = os.path.basename(os.path.normpath(root_resolved))
    rp = importlib.import_module(root_package)
    site_map = rp.apply_routes(web_app, render_template, global_cache)

    return web_app

# apply cross-cutting concerns, e.g. authentication against a database
def _apply_configuration(web_app, config, app_store):
    print("Applying the configuration  to the web_app instance..")

    #@web_app.route("/")
    def check_cookie():
        print("Req-Headers:", request.access_control_request_headers)

# everything executed when module is imported (initialization)

if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import' from another program.")
    # raise error?