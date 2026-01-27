"""Application Services - Orquestación de casos de uso

Implementa la capa de aplicación: coordina Domain Models con Infrastructure.
Cada servicio tiene una responsabilidad clara (SRP).
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from ..domain.models import (
    DiagramValidation,
    StoredDiagram,
    GenerationDomainError,
    ValidationDomainError,
)
from ..infrastructure.validator import DiagramValidator
from ..infrastructure.generator import DiagramGenerator
from ..infrastructure.storage import DiagramStorage
from ..infrastructure.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Repository Pattern (Dependency Inversion)
# ============================================================================


class DiagramRepository(ABC):
    """Abstract repository - Define el contrato que debe cumplir cualquier implementación"""

    @abstractmethod
    def save(self, diagram: StoredDiagram) -> bool:
        """Guardar diagrama"""
        pass

    @abstractmethod
    def get(self, diagram_id: str) -> Optional[StoredDiagram]:
        """Obtener diagrama por ID"""
        pass

    @abstractmethod
    def list_recent(self, limit: int = 10) -> list[StoredDiagram]:
        """Listar diagramas recientes"""
        pass

    @abstractmethod
    def delete(self, diagram_id: str) -> bool:
        """Eliminar diagrama"""
        pass


class DiagramRepositoryImpl(DiagramRepository):
    """Implementación del repositorio usando storage.py"""

    def __init__(self, storage: DiagramStorage):
        self.storage = storage

    def save(self, diagram: StoredDiagram) -> bool:
        """Guardar diagrama"""
        try:
            self.storage.save_diagram(
                diagram.diagram_id,
                diagram.metadata,
                diagram.code,
                diagram.file_paths,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save diagram: {str(e)}")
            return False

    def get(self, diagram_id: str) -> Optional[StoredDiagram]:
        """Obtener diagrama por ID"""
        try:
            return self.storage.get_diagram(diagram_id)
        except Exception as e:
            logger.error(f"Failed to get diagram: {str(e)}")
            return None

    def list_recent(self, limit: int = 10) -> list[StoredDiagram]:
        """Listar diagramas recientes"""
        try:
            diagrams = self.storage.list_diagrams()
            return diagrams[:limit]
        except Exception as e:
            logger.error(f"Failed to list diagrams: {str(e)}")
            return []

    def delete(self, diagram_id: str) -> bool:
        """Eliminar diagrama"""
        try:
            self.storage.delete_diagram(diagram_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete diagram: {str(e)}")
            return False


# ============================================================================
# Application Services (Single Responsibility)
# ============================================================================


class DiagramValidationService:
    """Servicio: Validar diagramas

    Responsabilidad única: Ejecutar validación AST y retornar resultado.
    """

    def __init__(self, validator: DiagramValidator):
        self.validator = validator

    def validate(self, code: str) -> DiagramValidation:
        """Validar código Python de diagrama

        Args:
            code: Python code to validate

        Returns:
            DiagramValidation: Resultado de validación

        Raises:
            ValidationDomainError: Si hay errores críticos
        """
        try:
            validation = self.validator.validate(code)

            if not validation.is_valid and validation.errors:
                logger.warning(f"Validation failed with {len(validation.errors)} errors")

            return validation

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise ValidationDomainError(f"Validation failed: {str(e)}")


class DiagramGenerationService:
    """Servicio: Generar diagramas

    Responsabilidad única: Orquestar el proceso de generación.
    """

    def __init__(
        self,
        generator: DiagramGenerator,
        validator: DiagramValidator,
        repository: DiagramRepository,
    ):
        self.generator = generator
        self.validator = validator
        self.repository = repository
        self.validation_service = DiagramValidationService(validator)

    def generate_diagram(
        self, code: str, diagram_name: str, validate_first: bool = True
    ) -> Dict[str, Any]:
        """Generar diagrama desde código Python

        Flujo:
        1. Validar código (opcional)
        2. Generar imágenes
        3. Guardar diagrama
        4. Retornar resultado

        Args:
            code: Python code
            diagram_name: Diagram name
            validate_first: Whether to validate before generating

        Returns:
            dict: Generation result

        Raises:
            GenerationDomainError: Si hay errores en la generación
        """
        try:
            # 1. Validar si es requerido
            validation = None
            if validate_first:
                validation = self.validation_service.validate(code)
                if not validation.is_valid and validation.errors:
                    raise GenerationDomainError(
                        f"Code validation failed: {validation.errors[0].message}"
                    )

            # 2. Generar diagramas
            output_files = self.generator.generate(
                code, diagram_name, settings.output_formats
            )

            if not output_files:
                raise GenerationDomainError("No output files generated")

            logger.info(f"✅ Diagram generated: {diagram_name}")

            return {
                "success": True,
                "output_files": output_files,
                "validation": validation.dict() if validation else None,
            }

        except GenerationDomainError:
            raise
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise GenerationDomainError(f"Generation failed: {str(e)}")

    def get_diagram(self, diagram_id: str) -> Optional[StoredDiagram]:
        """Obtener diagrama almacenado"""
        return self.repository.get(diagram_id)

    def delete_diagram(self, diagram_id: str) -> bool:
        """Eliminar diagrama"""
        return self.repository.delete(diagram_id)


class NaturalLanguageDiagramService:
    """Servicio: Generar diagramas desde lenguaje natural

    Responsabilidad única: Orquestar la pipeline de IA.
    """

    def __init__(
        self, generation_service: DiagramGenerationService, nl_processor_fn: Any
    ):
        self.generation_service = generation_service
        self.nl_processor_fn = nl_processor_fn

    def generate_from_description(
        self, description: str, diagram_name: str
    ) -> Dict[str, Any]:
        """Generar diagrama desde descripción en lenguaje natural

        Flujo:
        1. Procesar descripción con IA → Blueprint + Code
        2. Generar diagrama del código
        3. Retornar resultado

        Args:
            description: Natural language description
            diagram_name: Diagram name

        Returns:
            dict: Generation result with blueprint and code
        """
        try:
            logger.info(f"🤖 Generating from description: {diagram_name}")

            # 1. Procesar con IA usando la función callable
            nl_result = self.nl_processor_fn(
                description=description, diagram_name=diagram_name
            )

            blueprint = nl_result.get("blueprint", "")
            code = nl_result.get("code", "")

            if not code:
                raise GenerationDomainError("No code generated from description")

            # 2. Generar diagrama
            diagram_result = self.generation_service.generate_diagram(
                code, diagram_name, validate_first=True
            )

            return {
                "success": diagram_result["success"],
                "blueprint": blueprint,
                "code": code,
                "output_files": diagram_result.get("output_files", {}),
                "validation": diagram_result.get("validation"),
            }

        except Exception as e:
            logger.error(f"NL generation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "blueprint": None,
                "code": None,
            }


# ============================================================================
# Service Initialization (Factory)
# ============================================================================


def create_diagram_generation_service() -> DiagramGenerationService:
    """Factory para crear DiagramGenerationService con todas sus dependencias"""
    validator = DiagramValidator()
    generator = DiagramGenerator()
    storage = DiagramStorage()
    repository = DiagramRepositoryImpl(storage)

    return DiagramGenerationService(generator, validator, repository)


def create_nl_diagram_service(nl_processor: Any) -> NaturalLanguageDiagramService:
    """Factory para crear NaturalLanguageDiagramService"""
    generation_service = create_diagram_generation_service()
    return NaturalLanguageDiagramService(generation_service, nl_processor)
