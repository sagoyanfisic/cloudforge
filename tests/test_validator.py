"""Tests for diagram validator"""

import pytest
from src.validator import DiagramValidator


@pytest.fixture
def validator():
    """Create validator instance"""
    return DiagramValidator()


def test_valid_diagram_code(validator):
    """Test validation of valid diagram code"""
    code = """
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb

with Diagram("Test", show=False):
    lambda_func = Lambda("Function")
    db = Dynamodb("Database")
    lambda_func >> db
"""
    validation = validator.validate(code)
    assert validation.is_valid
    assert len(validation.errors) == 0


def test_syntax_error_detection(validator):
    """Test detection of syntax errors"""
    code = """
from diagrams import Diagram
from diagrams.aws.compute import Lambda

with Diagram("Test", show=False)
    lambda_func = Lambda("Function")
"""
    validation = validator.validate(code)
    assert not validation.is_valid
    assert len(validation.errors) > 0
    assert validation.errors[0].field == "syntax"


def test_component_count(validator):
    """Test component counting"""
    code = """
from diagrams import Diagram
from diagrams.aws.compute import Lambda, EC2
from diagrams.aws.database import Dynamodb

with Diagram("Test", show=False):
    lambda_func = Lambda("Function")
    ec2 = EC2("Server")
    db = Dynamodb("Database")
"""
    validation = validator.validate(code)
    assert validation.component_count > 0


def test_relationship_counting(validator):
    """Test relationship counting"""
    code = """
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb

with Diagram("Test", show=False):
    lambda_func = Lambda("Function")
    db = Dynamodb("Database")
    lambda_func >> db
"""
    validation = validator.validate(code)
    assert validation.relationship_count == 1


def test_security_warning_exec(validator):
    """Test security warning for exec"""
    code = """
from diagrams import Diagram

with Diagram("Test", show=False):
    exec("print('hi')")
"""
    validation = validator.validate(code)
    assert len(validation.warnings) > 0
    assert validation.warnings[0].field == "security"


def test_security_warning_file_operations(validator):
    """Test security warning for file operations"""
    code = """
from diagrams import Diagram

with Diagram("Test", show=False):
    with open("file.txt", "w") as f:
        f.write("test")
"""
    validation = validator.validate(code)
    assert len(validation.warnings) > 0
    assert validation.warnings[0].field == "security"


def test_unknown_component_warning(validator):
    """Test warning for unknown components"""
    code = """
from diagrams.aws.unknown import UnknownComponent

with Diagram("Test", show=False):
    component = UnknownComponent("Test")
"""
    validation = validator.validate(code)
    # Should still pass validation but with warnings
    assert validation.is_valid or len(validation.warnings) > 0
