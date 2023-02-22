# Module initialization: anything that cannot be injected via config.yml, e.g. routes (which must be "decorated"); as 
# this is passed to the 'Deployer' class, some conventions must be met, however. Memento: routes are similar to 
# openapi.json structure, but API is deployed separately!

site_map = {
    "Menue": {"url": "/menue", "template": "menue.html", "methods": ["GET"]},
    "My Acasa": {"url": "/settings", "template": "settings.html", "methods": ["GET"]}
}

def apply_routes(asgi_RT, render_func, ctx_cache):
    """
        Function must be names exactly like this!
    Args:
        asgi_RT (_type_): An ASGI runtime that provides a 'route' function
        render_func (_type_): A function capable to render a template.
        ctx_cache (_type_): An object that is passed to the template renderer.

    Returns:
        _type_: _description_
    """
    @asgi_RT.route('/', methods=['GET', 'POST', 'PUT'])
    async def index():
        return await render_func(["index.html"], site_map=site_map) 
    
    menue = site_map["Menue"]
    @asgi_RT.route(menue["url"], methods=menue["methods"])
    async def menue_func():
        return await render_func([menue["template"]], site_map=site_map, prods=ctx_cache['prods'])

    settings = site_map["My Acasa"]
    @asgi_RT.route(settings["url"], methods=settings["methods"])
    async def settings_func():
        return await render_func([settings["template"]], site_map=site_map, user_settings=ctx_cache['user_settings'])
    
    return site_map
