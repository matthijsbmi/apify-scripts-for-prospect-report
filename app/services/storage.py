"""
Storage service for data persistence.

This module provides storage service interfaces and implementations,
including an in-memory storage service with optional file persistence.
"""

import abc
import copy
import json
import os
import threading
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, Type, Union, cast
from uuid import UUID

from pydantic import BaseModel

from app.models.data import (
    Prospect, Analysis, ActorExecution, AnalysisParameters, AnalysisStatus,
    LinkedInData, SocialMediaData, CompanyData, ProspectAnalysisResponse,
    CostBreakdown, ExecutionMetadata, ConfidenceScores, KeyInsight
)
from app.core.config import settings


# Define type variable for generic storage operations
T = TypeVar('T', bound=BaseModel)


class StorageInterface(Generic[T], abc.ABC):
    """Abstract interface for storage operations."""
    
    @abc.abstractmethod
    def create(self, item: T) -> T:
        """Create a new item."""
        pass
    
    @abc.abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Get an item by ID."""
        pass
    
    @abc.abstractmethod
    def update(self, id: str, item: T) -> Optional[T]:
        """Update an existing item."""
        pass
    
    @abc.abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an item by ID."""
        pass
    
    @abc.abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """List items with pagination."""
        pass
    
    @abc.abstractmethod
    def filter(self, query: Dict[str, Any]) -> List[T]:
        """Filter items by query parameters."""
        pass
    
    @abc.abstractmethod
    def count(self) -> int:
        """Count total items."""
        pass


class InMemoryStorageService:
    """
    In-memory storage service with optional file persistence.
    
    This service stores data in memory and optionally persists to JSON files.
    It provides storage for all model types defined in app/models/data.py.
    """
    
    def __init__(self, persistence_dir: Optional[str] = None):
        """
        Initialize the storage service.
        
        Args:
            persistence_dir: Directory for file persistence. If None, no persistence.
        """
        self.persistence_dir = persistence_dir
        
        # Initialize in-memory storage
        self._prospects: Dict[str, Prospect] = {}
        self._analyses: Dict[str, Analysis] = {}
        self._actor_executions: Dict[str, ActorExecution] = {}
        self._analysis_results: Dict[str, ProspectAnalysisResponse] = {}
        
        # Locks for thread safety
        self._prospect_lock = threading.RLock()
        self._analysis_lock = threading.RLock()
        self._execution_lock = threading.RLock()
        self._result_lock = threading.RLock()
        
        # Load data from files if persistence directory exists
        if self.persistence_dir and os.path.exists(self.persistence_dir):
            self._load_from_files()
    
    def _json_serialize(self, obj: Any) -> Any:
        """
        Custom JSON serializer for handling special types.
        
        Args:
            obj: Object to serialize.
            
        Returns:
            JSON serializable value.
        """
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _ensure_persistence_dir(self) -> None:
        """Ensure persistence directory exists."""
        if self.persistence_dir:
            os.makedirs(self.persistence_dir, exist_ok=True)
    
    def _save_to_file(self, filename: str, data: Dict[str, Any]) -> None:
        """
        Save data to file.
        
        Args:
            filename: Name of the file.
            data: Data to save.
        """
        if not self.persistence_dir:
            return
        
        self._ensure_persistence_dir()
        file_path = os.path.join(self.persistence_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, default=self._json_serialize, indent=2)
        except Exception as e:
            # Log but don't fail on persistence errors
            print(f"Error saving to file {file_path}: {e}")
    
    def _load_from_file(self, filename: str, model_class: Type[T]) -> Dict[str, T]:
        """
        Load data from file.
        
        Args:
            filename: Name of the file.
            model_class: Model class for deserialization.
            
        Returns:
            Dictionary of deserialized objects.
        """
        if not self.persistence_dir:
            return {}
        
        file_path = os.path.join(self.persistence_dir, filename)
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {
                    id: model_class.model_validate(item)
                    for id, item in data.items()
                }
        except Exception as e:
            print(f"Error loading from file {file_path}: {e}")
            return {}
    
    def _load_from_files(self) -> None:
        """Load all data from persistence files."""
        with self._prospect_lock:
            self._prospects = self._load_from_file('prospects.json', Prospect)
        
        with self._analysis_lock:
            self._analyses = self._load_from_file('analyses.json', Analysis)
        
        with self._execution_lock:
            self._actor_executions = self._load_from_file('executions.json', ActorExecution)
        
        with self._result_lock:
            self._analysis_results = self._load_from_file(
                'results.json', ProspectAnalysisResponse
            )
    
    def _save_all(self) -> None:
        """Save all data to persistence files."""
        if not self.persistence_dir:
            return
        
        with self._prospect_lock:
            self._save_to_file('prospects.json', self._prospects)
        
        with self._analysis_lock:
            self._save_to_file('analyses.json', self._analyses)
        
        with self._execution_lock:
            self._save_to_file('executions.json', self._actor_executions)
        
        with self._result_lock:
            self._save_to_file('results.json', self._analysis_results)
    
    # Prospect methods
    def create_prospect(self, prospect: Prospect) -> Prospect:
        """
        Create a new prospect.
        
        Args:
            prospect: Prospect to create.
            
        Returns:
            Created prospect.
        """
        with self._prospect_lock:
            # Make a copy to avoid external modifications
            prospect_copy = copy.deepcopy(prospect)
            self._prospects[prospect.id] = prospect_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('prospects.json', self._prospects)
            
            return prospect_copy
    
    def get_prospect(self, prospect_id: str) -> Optional[Prospect]:
        """
        Get a prospect by ID.
        
        Args:
            prospect_id: ID of the prospect.
            
        Returns:
            Prospect if found, None otherwise.
        """
        with self._prospect_lock:
            prospect = self._prospects.get(prospect_id)
            if prospect:
                return copy.deepcopy(prospect)
            return None
    
    def update_prospect(self, prospect_id: str, prospect: Prospect) -> Optional[Prospect]:
        """
        Update an existing prospect.
        
        Args:
            prospect_id: ID of the prospect to update.
            prospect: Updated prospect data.
            
        Returns:
            Updated prospect if found, None otherwise.
        """
        with self._prospect_lock:
            if prospect_id not in self._prospects:
                return None
            
            # Make a copy to avoid external modifications
            prospect_copy = copy.deepcopy(prospect)
            prospect_copy.updated_at = datetime.now()
            self._prospects[prospect_id] = prospect_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('prospects.json', self._prospects)
            
            return prospect_copy
    
    def delete_prospect(self, prospect_id: str) -> bool:
        """
        Delete a prospect by ID.
        
        Args:
            prospect_id: ID of the prospect to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._prospect_lock:
            if prospect_id not in self._prospects:
                return False
            
            del self._prospects[prospect_id]
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('prospects.json', self._prospects)
            
            return True
    
    def list_prospects(self, skip: int = 0, limit: int = 100) -> List[Prospect]:
        """
        List prospects with pagination.
        
        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            
        Returns:
            List of prospects.
        """
        with self._prospect_lock:
            prospects = list(self._prospects.values())
            return copy.deepcopy(prospects[skip:skip + limit])
    
    def filter_prospects(self, query: Dict[str, Any]) -> List[Prospect]:
        """
        Filter prospects by query parameters.
        
        Args:
            query: Dictionary of field names and values to filter by.
            
        Returns:
            List of matching prospects.
        """
        with self._prospect_lock:
            result = []
            
            for prospect in self._prospects.values():
                match = True
                for key, value in query.items():
                    if hasattr(prospect, key):
                        if getattr(prospect, key) != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                
                if match:
                    result.append(copy.deepcopy(prospect))
            
            return result
    
    def count_prospects(self) -> int:
        """
        Count total prospects.
        
        Returns:
            Number of prospects.
        """
        with self._prospect_lock:
            return len(self._prospects)
    
    # Analysis methods
    def create_analysis(self, analysis: Analysis) -> Analysis:
        """
        Create a new analysis.
        
        Args:
            analysis: Analysis to create.
            
        Returns:
            Created analysis.
        """
        with self._analysis_lock:
            # Make a copy to avoid external modifications
            analysis_copy = copy.deepcopy(analysis)
            self._analyses[analysis.id] = analysis_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('analyses.json', self._analyses)
            
            return analysis_copy
    
    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """
        Get an analysis by ID.
        
        Args:
            analysis_id: ID of the analysis.
            
        Returns:
            Analysis if found, None otherwise.
        """
        with self._analysis_lock:
            analysis = self._analyses.get(analysis_id)
            if analysis:
                return copy.deepcopy(analysis)
            return None
    
    def update_analysis(self, analysis_id: str, analysis: Analysis) -> Optional[Analysis]:
        """
        Update an existing analysis.
        
        Args:
            analysis_id: ID of the analysis to update.
            analysis: Updated analysis data.
            
        Returns:
            Updated analysis if found, None otherwise.
        """
        with self._analysis_lock:
            if analysis_id not in self._analyses:
                return None
            
            # Make a copy to avoid external modifications
            analysis_copy = copy.deepcopy(analysis)
            self._analyses[analysis_id] = analysis_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('analyses.json', self._analyses)
            
            return analysis_copy
    
    def update_analysis_status(
        self, analysis_id: str, status: AnalysisStatus, error: Optional[str] = None
    ) -> Optional[Analysis]:
        """
        Update analysis status.
        
        Args:
            analysis_id: ID of the analysis.
            status: New status.
            error: Error message if status is FAILED.
            
        Returns:
            Updated analysis if found, None otherwise.
        """
        with self._analysis_lock:
            analysis = self._analyses.get(analysis_id)
            if not analysis:
                return None
            
            analysis_copy = copy.deepcopy(analysis)
            analysis_copy.status = status
            
            if status == AnalysisStatus.COMPLETED:
                analysis_copy.completed_at = datetime.now()
            
            if error and status == AnalysisStatus.FAILED:
                analysis_copy.error = error
            
            self._analyses[analysis_id] = analysis_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('analyses.json', self._analyses)
            
            return analysis_copy
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis by ID.
        
        Args:
            analysis_id: ID of the analysis to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._analysis_lock:
            if analysis_id not in self._analyses:
                return False
            
            del self._analyses[analysis_id]
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('analyses.json', self._analyses)
            
            return True
    
    def list_analyses(self, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """
        List analyses with pagination.
        
        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            
        Returns:
            List of analyses.
        """
        with self._analysis_lock:
            analyses = list(self._analyses.values())
            return copy.deepcopy(analyses[skip:skip + limit])
    
    def filter_analyses(self, query: Dict[str, Any]) -> List[Analysis]:
        """
        Filter analyses by query parameters.
        
        Args:
            query: Dictionary of field names and values to filter by.
            
        Returns:
            List of matching analyses.
        """
        with self._analysis_lock:
            result = []
            
            for analysis in self._analyses.values():
                match = True
                for key, value in query.items():
                    if hasattr(analysis, key):
                        attr_value = getattr(analysis, key)
                        
                        if key == 'status' and isinstance(value, str):
                            # Handle Enum comparison
                            if str(attr_value.value) != value:
                                match = False
                                break
                        elif attr_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                
                if match:
                    result.append(copy.deepcopy(analysis))
            
            return result
    
    def count_analyses(self) -> int:
        """
        Count total analyses.
        
        Returns:
            Number of analyses.
        """
        with self._analysis_lock:
            return len(self._analyses)
    
    # Actor execution methods
    def create_execution(self, execution: ActorExecution) -> ActorExecution:
        """
        Create a new actor execution record.
        
        Args:
            execution: Execution to create.
            
        Returns:
            Created execution.
        """
        with self._execution_lock:
            # Make a copy to avoid external modifications
            execution_copy = copy.deepcopy(execution)
            self._actor_executions[execution.run_id] = execution_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('executions.json', self._actor_executions)
            
            return execution_copy
    
    def get_execution(self, run_id: str) -> Optional[ActorExecution]:
        """
        Get an execution by run ID.
        
        Args:
            run_id: ID of the actor run.
            
        Returns:
            Execution if found, None otherwise.
        """
        with self._execution_lock:
            execution = self._actor_executions.get(run_id)
            if execution:
                return copy.deepcopy(execution)
            return None
    
    def update_execution(
        self, run_id: str, execution: ActorExecution
    ) -> Optional[ActorExecution]:
        """
        Update an existing execution.
        
        Args:
            run_id: ID of the execution to update.
            execution: Updated execution data.
            
        Returns:
            Updated execution if found, None otherwise.
        """
        with self._execution_lock:
            if run_id not in self._actor_executions:
                return None
            
            # Make a copy to avoid external modifications
            execution_copy = copy.deepcopy(execution)
            self._actor_executions[run_id] = execution_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('executions.json', self._actor_executions)
            
            return execution_copy
    
    def delete_execution(self, run_id: str) -> bool:
        """
        Delete an execution by run ID.
        
        Args:
            run_id: ID of the execution to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._execution_lock:
            if run_id not in self._actor_executions:
                return False
            
            del self._actor_executions[run_id]
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('executions.json', self._actor_executions)
            
            return True
    
    def list_executions(self, skip: int = 0, limit: int = 100) -> List[ActorExecution]:
        """
        List executions with pagination.
        
        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            
        Returns:
            List of executions.
        """
        with self._execution_lock:
            executions = list(self._actor_executions.values())
            return copy.deepcopy(executions[skip:skip + limit])
    
    def filter_executions(self, query: Dict[str, Any]) -> List[ActorExecution]:
        """
        Filter executions by query parameters.
        
        Args:
            query: Dictionary of field names and values to filter by.
            
        Returns:
            List of matching executions.
        """
        with self._execution_lock:
            result = []
            
            for execution in self._actor_executions.values():
                match = True
                for key, value in query.items():
                    if hasattr(execution, key):
                        if getattr(execution, key) != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                
                if match:
                    result.append(copy.deepcopy(execution))
            
            return result
    
    def filter_executions_by_analysis(self, analysis_id: str) -> List[ActorExecution]:
        """
        Get all executions for an analysis.
        
        Args:
            analysis_id: ID of the analysis.
            
        Returns:
            List of executions for the analysis.
        """
        return self.filter_executions({"analysis_id": analysis_id})
    
    def count_executions(self) -> int:
        """
        Count total executions.
        
        Returns:
            Number of executions.
        """
        with self._execution_lock:
            return len(self._actor_executions)
    
    # Analysis result methods
    def save_analysis_result(
        self, result: ProspectAnalysisResponse
    ) -> ProspectAnalysisResponse:
        """
        Save an analysis result.
        
        Args:
            result: Analysis result to save.
            
        Returns:
            Saved result.
        """
        with self._result_lock:
            # Make a copy to avoid external modifications
            result_copy = copy.deepcopy(result)
            self._analysis_results[result.analysis_id] = result_copy
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('results.json', self._analysis_results)
            
            return result_copy
    
    def get_analysis_result(self, analysis_id: str) -> Optional[ProspectAnalysisResponse]:
        """
        Get an analysis result by analysis ID.
        
        Args:
            analysis_id: ID of the analysis.
            
        Returns:
            Result if found, None otherwise.
        """
        with self._result_lock:
            result = self._analysis_results.get(analysis_id)
            if result:
                return copy.deepcopy(result)
            return None
    
    def delete_analysis_result(self, analysis_id: str) -> bool:
        """
        Delete an analysis result by analysis ID.
        
        Args:
            analysis_id: ID of the analysis result to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._result_lock:
            if analysis_id not in self._analysis_results:
                return False
            
            del self._analysis_results[analysis_id]
            
            # Update persistence
            if self.persistence_dir:
                self._save_to_file('results.json', self._analysis_results)
            
            return True
    
    def list_analysis_results(
        self, skip: int = 0, limit: int = 100
    ) -> List[ProspectAnalysisResponse]:
        """
        List analysis results with pagination.
        
        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            
        Returns:
            List of analysis results.
        """
        with self._result_lock:
            results = list(self._analysis_results.values())
            return copy.deepcopy(results[skip:skip + limit])
    
    def get_analysis_result_by_prospect(
        self, prospect_id: str
    ) -> List[ProspectAnalysisResponse]:
        """
        Get analysis results for a prospect.
        
        Args:
            prospect_id: ID of the prospect.
            
        Returns:
            List of analysis results for the prospect.
        """
        with self._result_lock:
            results = []
            
            for result in self._analysis_results.values():
                if result.prospect_id == prospect_id:
                    results.append(copy.deepcopy(result))
            
            return results
    
    def count_analysis_results(self) -> int:
        """
        Count total analysis results.
        
        Returns:
            Number of analysis results.
        """
        with self._result_lock:
            return len(self._analysis_results)
    
    def clear(self) -> None:
        """Clear all stored data (for testing purposes)."""
        with self._prospect_lock:
            self._prospects.clear()
        
        with self._analysis_lock:
            self._analyses.clear()
        
        with self._execution_lock:
            self._actor_executions.clear()
        
        with self._result_lock:
            self._analysis_results.clear()
        
        # Clear persistence files
        if self.persistence_dir:
            self._save_all()


# Singleton instance
_storage_service: Optional[InMemoryStorageService] = None


def get_storage_service() -> InMemoryStorageService:
    """
    Get the singleton storage service instance.
    
    Returns:
        Storage service instance.
    """
    global _storage_service
    
    if _storage_service is None:
        persistence_dir = None
        
        # Check if persistence is enabled in settings
        if hasattr(settings, 'storage_persistence_enabled') and settings.storage_persistence_enabled:
            persistence_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data'
            )
        
        _storage_service = InMemoryStorageService(persistence_dir)
    
    return _storage_service 