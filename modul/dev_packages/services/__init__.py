from . import python_service
from . import ruby_service
from . import node_service
from . import php_service
from . import rust_service
from . import go_service
from . import dotnet_service

SERVICES = {
    'pip': python_service,
    'gem': ruby_service,
    'npm': node_service,
    'composer': php_service,
    'cargo': rust_service,
    'go': go_service,
    'dotnet': dotnet_service,
}


