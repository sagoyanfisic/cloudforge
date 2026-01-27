"""Diagram validation module"""

import ast
import re
from typing import Any
from ..domain.models import ValidationError, DiagramValidation
from .config import settings


class DiagramValidator:
    """Validates diagram code and structure"""

    def __init__(self) -> None:
        self.aws_components = self._load_aws_components()

    def _load_aws_components(self) -> set[str]:
        """Load valid AWS component names"""
        return {
            "APIGateway",
            "Lambda",
            "Dynamodb",
            "S3",
            "EC2",
            "RDS",
            "ElastiCache",
            "SQS",
            "SNS",
            "CloudFront",
            "Route53",
            "IAM",
            "CloudWatch",
            "VPC",
            "SecurityGroup",
            "ELB",
            "ALB",
            "NLB",
            "AutoScaling",
            "ECS",
            "EKS",
            "CodeDeploy",
            "CodePipeline",
            "CodeBuild",
            "KMS",
        }

    def validate(self, code: str) -> DiagramValidation:
        """Validate diagram code"""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Syntax validation
        syntax_errors = self._validate_syntax(code)
        errors.extend(syntax_errors)

        # Component validation
        component_errors, component_count = self._validate_components(code)
        errors.extend(component_errors)

        # Security validation
        security_warnings = self._validate_security(code)
        warnings.extend(security_warnings)

        # Size validation
        if component_count > settings.max_components:
            errors.append(
                ValidationError(
                    field="components",
                    message=f"Too many components: {component_count} > {settings.max_components}",
                    severity="error",
                )
            )

        # Relationship validation
        relationship_count = self._count_relationships(code)
        if relationship_count > settings.max_relationships:
            errors.append(
                ValidationError(
                    field="relationships",
                    message=f"Too many relationships: {relationship_count} > {settings.max_relationships}",
                    severity="error",
                )
            )

        return DiagramValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            component_count=component_count,
            relationship_count=relationship_count,
        )

    def _validate_syntax(self, code: str) -> list[ValidationError]:
        """Validate Python syntax"""
        errors: list[ValidationError] = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(
                ValidationError(
                    field="syntax",
                    message=f"Syntax error at line {e.lineno}: {e.msg}",
                    severity="error",
                )
            )
        except Exception as e:
            errors.append(
                ValidationError(
                    field="syntax",
                    message=f"Parse error: {str(e)}",
                    severity="error",
                )
            )
        return errors

    def _validate_components(self, code: str) -> tuple[list[ValidationError], int]:
        """Validate AWS components used"""
        errors: list[ValidationError] = []
        component_count = 0

        # Find all class instantiations
        pattern = r"from diagrams\.aws\.(\w+) import\s+(\w+(?:\s*,\s*\w+)*)"
        matches = re.finditer(pattern, code)

        found_components = set()
        for match in matches:
            components = match.group(2).split(",")
            for comp in components:
                comp = comp.strip()
                if comp and comp not in self.aws_components:
                    errors.append(
                        ValidationError(
                            field="components",
                            message=f"Unknown component: {comp}",
                            severity="warning",
                        )
                    )
                found_components.add(comp)

        # Count instantiations
        instantiation_pattern = r"(\w+)\s*\(['\"]"
        instantiations = re.findall(instantiation_pattern, code)
        component_count = len([x for x in instantiations if x in found_components])

        return errors, component_count

    def _count_relationships(self, code: str) -> int:
        """Count relationships (>> operators) in the diagram"""
        # Count all >> operators which represent relationships
        return len(re.findall(r">>", code))

    def _validate_security(self, code: str) -> list[ValidationError]:
        """Validate security concerns"""
        warnings: list[ValidationError] = []

        # Check for exec, eval, or other dangerous functions
        dangerous_functions = ["exec", "eval", "__import__"]
        for func in dangerous_functions:
            if func in code:
                warnings.append(
                    ValidationError(
                        field="security",
                        message=f"Dangerous function detected: {func}",
                        severity="warning",
                    )
                )

        # Check for file operations
        if re.search(r"\bopen\s*\(", code):
            warnings.append(
                ValidationError(
                    field="security",
                    message="File operations detected in diagram code",
                    severity="warning",
                )
            )

        return warnings
