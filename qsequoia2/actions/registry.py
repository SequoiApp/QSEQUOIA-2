import pkgutil
import importlib

def load_actions():
    actions = {}

    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name == "registry":
            continue

        module = importlib.import_module(f"{__name__}.{module_name}")

        label = getattr(module, "LABEL", None)
        run = getattr(module, "run", None)

        if label and callable(run):
            actions[label] = run

    return actions
