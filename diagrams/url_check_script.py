import os
from diagrams import Diagram

os.makedirs("output", exist_ok=True)

with Diagram("No Architecture Found", show=False, filename="/app/diagrams/url_check"):
    pass