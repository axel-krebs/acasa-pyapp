# Shared web objects
from abc import ABC, abstractmethod
import os
from pathlib import Path
from quart import Quart, session, render_template
import uvicorn
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
    """_summary_
        This serves as a helper class to share a caching structure between modules 
        resp. between the Deployment class and the deployables; in the future, it 
        should be replaced by a caching framework resp. distributed cache. Like the
        class Documentstore, it can then serve as an interface.
    """
    def __init__(self):
        self._protected_dict = dict()

    def __getitem__(self, key):
        return self._protected_dict[key]
    
    def __setitem__(self, key, value):
        self._protected_dict[key] = value
        return self._protected_dict[key]

class Documentstore(ABC):
    """_summary_
        An "interface" for the injected document store, th. i. 
        what the web app expects the underlying implementation 
        to be able to deliver.
    Args:
        ABC (_type_): _description_
    """
    
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def test_impl(self):
         raise NotImplementedError("Should not happen..")

    @abstractmethod
    def get_user_for_cookie(self, cookie):
        raise NotImplementedError("Should not happen..")
    
    @abstractmethod
    def create_user(self, name: str = "", email: str = ""):
        raise NotImplementedError("Should not happen..")


class Deployment(ABC):
    
    @abstractmethod
    def apply(rt: Quart, cache: ContextCache, render_func):
        raise NotImplementedError("Should not happen..")

class Deployer():
    """_summary_
        Basically a wrapper around the Quart web app, with some convenience methods, e.g. 'start' 
        or 'stop' the server resp. debug..
    Args:
        ABC (_type_): _description_
    """
    def __init__(self, web_app: Quart, host: str, port: int, global_cache: ContextCache):
        self._quart_inst = web_app
        self._host_name = host
        self._port_number = port
        self._ctx_cache = global_cache

        self._init_routes()
        
        #@quart_inst.before_request
        #def make_session_permanent():
        #    session.permanent = True

    def _init_routes(self):

        @self._quart_inst.route('/')
        async def index():
            return await render_template(["index.html"], cache_data = self._ctx_cache)

        # more
        
    def debug(self):
        self._quart_inst.run()

    def start_server(self):
        runner = uvicorn.run(self._quart_inst, host=self._host_name, port=self._port_number, log_level="info")
        print("Running {}".format(runner))

    def stop_server(self):
        pass

    def deploy(self, d: Deployment):
        """_summary_
        Principally, a variant of "inversion of control" 
        Args:
            d (Deployment): _description_
        """
        d.apply(self._quart_inst, self._ctx_cache, render_template)

def create_instance(root: Path = SCRIPT_PATH, doc_store: Documentstore = None, global_cache: ContextCache = None) -> Deployer:
    """_summary_
    A deployment must have a predefined structure, e.g. the config file 
    must be named 'config.yaml' and must have an entry 'quart' etc.

    Args:
        folder (Path, optional): _description_. Defaults to script path
    """
    if doc_store is None or doc_store.test_impl():
        raise RuntimeError("The document store implementation is not valid!")
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
    web_app = Quart(
        import_name = config["import_name"],
        #root_path = config["root_path"],
        root_path = root_resolved, # assume correct
        static_folder = static_path,
        static_url_path = config["static_url_path"],
        template_folder = template_path
    )
    return Deployer(web_app, host = config["host_name"], port=config["host_port"], global_cache=global_cache)

# everything executed when module is imported (initialization)

if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import'.")
    # raise error?