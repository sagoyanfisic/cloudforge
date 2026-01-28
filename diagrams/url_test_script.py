import os
from diagrams import Diagram

os.makedirs("output", exist_ok=True)

with Diagram("Empty Diagram - No Architecture Provided", show=False, filename="/app/diagrams/url_test", direction="TB"):
    pass