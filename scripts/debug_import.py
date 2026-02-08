import importlib
m = importlib.import_module('app.api.routes')
print('module_file:', m.__file__)
print('has_router:', hasattr(m, 'router'))
print('names:', [k for k in m.__dict__.keys() if not k.startswith('__')])
print('\n---- source ----')
print(open(m.__file__, 'r', encoding='utf-8').read())
