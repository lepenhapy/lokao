import sys
import pathlib
import traceback

# Ensure project root is on sys.path so `import app...` works when run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
try:
    import app.api.routes as routes
    print('imported OK, has router:', hasattr(routes, 'router'))
    print('router repr:', repr(getattr(routes, 'router', None)))
except Exception:
    traceback.print_exc()
    raise
